"""
llm_classifier.py - Interface with the LLM for species classification
======================================================================
Uses the Ollama API (local) for:
  1. Assigning species to existing functional groups.
  2. Creating new groups for unclassified species.
  3. Proposing group merges when limit exceeds.
"""

import json
import re
from typing import Optional

import requests

from config import (
    OLLAMA_API_URL,
    OLLAMA_MODEL,
    LLM_MAX_TOKENS,
    LLM_TEMPERATURE,
    OLLAMA_TIMEOUT,
    LLM_STREAMING,
    MAX_GROUPS,
    SCORING_CRITERIA,
)
from data_loader import species_to_text_list, groups_to_text


def _call_llm(system_prompt: str, user_prompt: str, stream: bool = False) -> str:
    """
    Generic LLM call via Ollama API.

    Parameters
    ----------
    system_prompt : str
        System instructions.
    user_prompt : str
        User message.
    stream : bool, optional
        If True, print tokens in real-time as they're generated. Default is False.

    Returns
    -------
    str
        Model response.
        
    Raises
    ------
    ConnectionError
        If unable to connect to Ollama.
    """
    # Combine system and user prompts
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "stream": stream,
        "temperature": LLM_TEMPERATURE,
    }
    
    try:
        response = requests.post(
            OLLAMA_API_URL,
            json=payload,
            timeout=OLLAMA_TIMEOUT,
            stream=stream,
        )
        response.raise_for_status()
        
        if stream:
            # Process streaming response
            full_response = ""
            print("\n  🤖 Model output:\n  ", end="", flush=True)
            for line in response.iter_lines():
                if line:
                    chunk = line.decode("utf-8") if isinstance(line, bytes) else line
                    data = json.loads(chunk)
                    token = data.get("response", "")
                    if token:
                        full_response += token
                        print(token, end="", flush=True)
            print("\n")  # New line after streaming
            return full_response
        else:
            # Non-streaming response
            result = response.json()
            return result.get("response", "")
    except requests.exceptions.ConnectionError as e:
        raise ConnectionError(
            f"Could not connect to Ollama at {OLLAMA_API_URL}. "
            f"Make sure Ollama is running: ollama serve\n"
            f"Error: {e}"
        ) from e
    except requests.exceptions.Timeout:
        raise TimeoutError(
            f"Timeout waiting for Ollama response (>{OLLAMA_TIMEOUT}s). "
            f"Try with a smaller model or increase OLLAMA_TIMEOUT."
        )
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Error in Ollama request: {e}") from e


def _extract_json_from_response(response: str) -> dict | list:
    """
    Extract JSON from LLM response, handling possible code blocks.
    Handles incomplete JSON by trying to close it automatically.
    Robust to truncated responses.

    Parameters
    ----------
    response : str
        Raw text from LLM response.

    Returns
    -------
    dict | list
        Parsed JSON object.
    """
    # Try to extract from ```json ... ``` block
    json_match = re.search(r"```json\s*(.*?)(?:\s*```|$)", response, re.DOTALL)
    if json_match:
        extracted = json_match.group(1)
        result = _try_parse_json(extracted)
        if result is not None:
            return result

    # Try to extract from generic ``` ... ``` block
    code_match = re.search(r"```\s*(.*?)(?:\s*```|$)", response, re.DOTALL)
    if code_match:
        extracted = code_match.group(1)
        result = _try_parse_json(extracted)
        if result is not None:
            return result

    # Try direct parsing (find first [ or {)
    for i, char in enumerate(response):
        if char in ("[", "{"):
            result = _try_parse_json(response[i:])
            if result is not None:
                return result

    raise ValueError(f"Could not extract JSON from response:\n{response[:500]}")


def _try_parse_json(text: str) -> dict | list | None:
    """
    Attempt to parse JSON from text, trying various recovery strategies
    for incomplete/truncated JSON.
    
    Parameters
    ----------
    text : str
        Text potentially containing JSON (may be incomplete).
    
    Returns
    -------
    dict | list | None
        Parsed JSON if successful, None otherwise.
    """
    # First, try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to fix incomplete JSON
    text_stripped = text.rstrip()
    
    # Remove trailing commas before closing brackets
    text_fixed = re.sub(r',(\s*[}\]])', r'\1', text_stripped)
    
    try:
        return json.loads(text_fixed)
    except json.JSONDecodeError:
        pass
    
    # Try to close incomplete JSON structures
    # Count unmatched braces/brackets
    open_braces = text_fixed.count('{') - text_fixed.count('}')
    open_brackets = text_fixed.count('[') - text_fixed.count(']')
    
    # Try closing with appropriate closing characters
    closing_str = '}' * max(0, open_braces) + ']' * max(0, open_brackets)
    
    try:
        return json.loads(text_fixed + closing_str)
    except json.JSONDecodeError:
        pass
    
    # Last resort: try to find the last complete JSON object/array in the text
    # Look backwards for the last closing brace/bracket that forms valid JSON
    for end_pos in range(len(text_fixed), 0, -1):
        for closing in ('}]', '}', ']'):
            test_text = text_fixed[:end_pos] + closing
            try:
                return json.loads(test_text)
            except json.JSONDecodeError:
                continue
    
    return None


def _deduplicate_assignments(result: dict | list) -> dict | list:
    """
    Remove duplicate species assignments, keeping only the first occurrence.
    
    Parameters
    ----------
    result : dict | list
        JSON response from LLM containing assignments.
    
    Returns
    -------
    dict | list
        Deduplicated result.
    """
    if isinstance(result, dict) and "assignments" in result:
        assignments = result.get("assignments", [])
        if assignments:
            seen_species = set()
            deduped = []
            removed = 0
            
            for assignment in assignments:
                sp_name = assignment.get("species", "").lower().strip()
                if sp_name and sp_name not in seen_species:
                    seen_species.add(sp_name)
                    deduped.append(assignment)
                elif sp_name:
                    removed += 1
            
            if removed > 0:
                print(f"    ⚠️  Removed {removed} duplicate species from model response")
            
            result["assignments"] = deduped
    
    return result


def _is_response_duplicate(current_response: dict | list, previous_response: dict | list) -> bool:
    """
    Check if the current LLM response is identical to the previous one.
    Used to skip processing if the model returns the same result for consecutive batches.
    
    Parameters
    ----------
    current_response : dict | list
        Current LLM response (parsed JSON).
    previous_response : dict | list
        Previous LLM response (parsed JSON).
    
    Returns
    -------
    bool
        True if responses are identical, False otherwise.
    """
    if previous_response is None:
        return False
    
    try:
        # Serialize to JSON string for comparison (ignores dict ordering)
        current_json = json.dumps(current_response, sort_keys=True)
        previous_json = json.dumps(previous_response, sort_keys=True)
        return current_json == previous_json
    except (TypeError, ValueError):
        # If serialization fails, they're not duplicates
        return False


# ═══════════════════════════════════════════════════════════════════════
# STEP 1: Assign species to existing groups
# ═══════════════════════════════════════════════════════════════════════

BATCH_SIZE = 187  # Species per LLM call (reduced by 25% from 250 for better stability)
                  # 187 ≈ 250 * 0.75


def classify_species_into_groups(
    species_text: str,
    groups_text: str,
    groups: list[dict],
) -> tuple[list[dict], list[str]]:
    """
    Use LLM to assign each species to an existing functional group.
    Processes in batches of BATCH_SIZE species to respect LLM limits.

    Parameters
    ----------
    species_text : str
        Formatted list of species as text.
    groups_text : str
        Formatted list of functional groups as text.
    groups : list[dict]
        Current functional groups (species lists are modified in-place).

    Returns
    -------
    tuple[list[dict], list[str]]
        - Updated groups with assigned species.
        - List of species names that could not be assigned.
    """
    # Split species list into individual lines
    species_lines = [l for l in species_text.strip().split("\n") if l.strip()]
    total = len(species_lines)

    # Split into batches
    batches = [
        species_lines[i : i + BATCH_SIZE]
        for i in range(0, total, BATCH_SIZE)
    ]
    n_batches = len(batches)
    print(f"[LLM] Classifying {total} species in {n_batches} batches of ~{BATCH_SIZE}...")

    system_prompt = """You are an expert marine ecologist in ecosystem modeling.
Your task is to assign species to existing functional groups based on their
ecological and functional characteristics.

RULES:
- Each species must be assigned to the group that best represents its functional role.
- If a species does NOT fit reasonably into any existing group, mark it as "unassigned".
- Prioritize trophic role and habitat over taxonomy.
- Respond ONLY with valid JSON, no additional text."""

    group_map = {g["group_id"]: i for i, g in enumerate(groups)}
    all_unassigned = []
    previous_result = None  # Track previous response to detect duplicates

    for batch_idx, batch in enumerate(batches, 1):
        batch_text = "\n".join(batch)
        user_prompt = f"""## CURRENT FUNCTIONAL GROUPS:
{groups_text}

## LIST OF SPECIES TO CLASSIFY (batch {batch_idx}/{n_batches}):
{batch_text}

## INSTRUCTION:
Assign each species to the group_id of the most appropriate functional group.
If it doesn't fit in any, use "unassigned".

Respond with JSON with this structure:
```json
{{
  "assignments": [
    {{"species": "scientific name", "group_id": "FG01", "reason": "brief justification"}},
    {{"species": "another species", "group_id": "unassigned", "reason": "reason"}}
  ]
}}
`"""

        print(f"  [Batch {batch_idx}/{n_batches}] Processing {len(batch)} species...")
        response = _call_llm(system_prompt, user_prompt, stream=LLM_STREAMING)
        result = _extract_json_from_response(response)
        result = _deduplicate_assignments(result)
        
        # Skip if response is identical to previous batch (model is repeating)
        if _is_response_duplicate(result, previous_result):
            print(f"  [Batch {batch_idx}/{n_batches}] ⏭️  SKIPPING - Response identical to previous batch")
            previous_result = result
            continue
        
        previous_result = result

        for assignment in result.get("assignments", []):
            sp = assignment["species"]
            gid = assignment["group_id"]

            if gid == "unassigned" or gid not in group_map:
                all_unassigned.append(sp)
            else:
                idx = group_map[gid]
                if sp not in groups[idx]["species"]:
                    groups[idx]["species"].append(sp)

        assigned_so_far = sum(len(g["species"]) for g in groups)
        print(f"  [Batch {batch_idx}/{n_batches}] Accumulated: {assigned_so_far} assigned, {len(all_unassigned)} unassigned")

    print(
        f"[LLM] Classification completed: "
        f"{sum(len(g['species']) for g in groups)} assigned, "
        f"{len(all_unassigned)} unassigned"
    )
    return groups, all_unassigned


# ═══════════════════════════════════════════════════════════════════════
# STEP 2: Create new groups for unclassified species
# ═══════════════════════════════════════════════════════════════════════

def create_groups_for_unassigned(
    unassigned_species: list[str],
    species_text: str,
    existing_groups: list[dict],
) -> list[dict]:
    """
    Usa el LLM para crear nuevos grupos funcionales para las especies no clasificadas.

    Parameters
    ----------
    unassigned_species : list[str]
        Nombres de especies sin grupo asignado.
    species_text : str
        Texto completo de todas las especies (para contexto).
    existing_groups : list[dict]
        Grupos existentes (para evitar duplicados).

    Returns
    -------
    list[dict]
        Lista de nuevos grupos funcionales creados.
    """
    if not unassigned_species:
        print("[LLM] No hay especies sin grupo. No se crean grupos nuevos.")
        return []

    existing_names = [g["group_name"] for g in existing_groups]
    next_id = len(existing_groups) + 1

    system_prompt = """You are an expert marine ecologist in ecosystem modeling.
Your task is to create NEW functional groups for species that don't fit in existing groups.

RULES:
- Each group must represent a specific FUNCTIONAL ROLE in the ecosystem.
- Group species by functional similarity (habitat + trophic level + ecological role).
- Avoid creating redundant groups with existing ones.
- Minimize new groups by clustering species when ecologically valid.
- Don't create more than 40 new groups per batch.
- Respond ONLY with valid JSON, no additional text."""

    # Process in batches
    batches = [
        unassigned_species[i : i + BATCH_SIZE]
        for i in range(0, len(unassigned_species), BATCH_SIZE)
    ]
    n_batches = len(batches)
    print(
        f"[LLM] Creating groups for {len(unassigned_species)} unclassified species "
        f"({n_batches} batches)..."
    )

    all_new_groups = []
    previous_result = None  # Track previous response to detect duplicates

    for batch_idx, batch in enumerate(batches, 1):
        unassigned_str = "\n".join(f"- {sp}" for sp in batch)
        current_next_id = next_id + len(all_new_groups)

        user_prompt = f"""## UNASSIGNED SPECIES (batch {batch_idx}/{n_batches}):
{unassigned_str}

## EXISTING GROUPS (to avoid redundancies):
{', '.join(existing_names + [g['group_name'] for g in all_new_groups])}

## INSTRUCTION:
Create the functional groups needed to classify these species.
Start IDs from FG{current_next_id:02d}.

Respond with JSON with this structure:
```json
{{
  "new_groups": [
    {{
      "group_id": "FG{current_next_id:02d}",
      "group_name": "Descriptive group name",
      "description": "Description of functional role in ecosystem",
      "characteristics": {{
        "habitat": "benthic/pelagic/demersal/coastal/terrestrial",
        "trophic_level": "carnivore/herbivore/omnivore/etc.",
        "size_class": "small/medium/large",
        "taxonomic_affinity": "main taxonomic group"
      }},
      "species": ["species1", "species2"]
    }}
  ]
}}
```"""

        print(f"  [Batch {batch_idx}/{n_batches}] Creating groups for {len(batch)} species...")
        response = _call_llm(system_prompt, user_prompt, stream=LLM_STREAMING)
        result = _extract_json_from_response(response)
        result = _deduplicate_assignments(result)
        
        # Skip if response is identical to previous batch (model is repeating)
        if _is_response_duplicate(result, previous_result):
            print(f"  [Batch {batch_idx}/{n_batches}] ⏭️  SKIPPING - Response identical to previous batch")
            previous_result = result
            continue
        
        previous_result = result

        new_groups = result.get("new_groups", [])
        all_new_groups.extend(new_groups)
        print(f"  [Batch {batch_idx}/{n_batches}] {len(new_groups)} new groups (total: {len(all_new_groups)})")

    print(f"[LLM] Created {len(all_new_groups)} new functional groups in total")
    return all_new_groups


# ═══════════════════════════════════════════════════════════════════════
# PASO 3: Evaluar importancia de los grupos
# ═══════════════════════════════════════════════════════════════════════

def evaluate_group_importance(
    groups: list[dict],
    species_df,
) -> list[dict]:
    """
    Usa el LLM para asignar puntajes de importancia a cada grupo funcional.

    Parameters
    ----------
    groups : list[dict]
        Todos los grupos funcionales.
    species_df : pd.DataFrame
        DataFrame de especies con sus atributos.

    Returns
    -------
    list[dict]
        Grupos con un campo 'importance_score' y 'score_breakdown' añadidos.
    """
    groups_text = groups_to_text(groups)
    criteria_text = "\n".join(
        f"- {k} (peso: {v['weight']}): {v['description']}"
        for k, v in SCORING_CRITERIA.items()
    )

    system_prompt = """Eres un ecólogo marino experto evaluando la importancia de grupos funcionales
para un modelo ecosistémico ATLANTIS del Golfo de California.

Evalúa cada grupo según los criterios proporcionados, asignando puntajes de 0.0 a 1.0.
El puntaje final es la suma ponderada.
Responde ÚNICAMENTE con un JSON válido."""

    user_prompt = f"""## GRUPOS FUNCIONALES:
{groups_text}

## CRITERIOS DE EVALUACIÓN:
{criteria_text}

## INSTRUCCIÓN:
Para cada grupo, asigna un puntaje (0.0-1.0) en cada criterio.
Calcula el puntaje total ponderado.

Responde con:
```json
{{
  "scores": [
    {{
      "group_id": "FG01",
      "score_breakdown": {{
        "species_richness": 0.8,
        "trophic_importance": 0.9,
        "commercial_value": 0.7,
        "ecological_role": 0.8,
        "conservation_status": 0.3,
        "uniqueness": 0.6
      }},
      "total_score": 0.75,
      "justification": "Breve justificación"
    }}
  ]
}}
```"""

    print("[LLM] Evaluando importancia de grupos funcionales...")
    response = _call_llm(system_prompt, user_prompt, stream=LLM_STREAMING)
    result = _extract_json_from_response(response)
    result = _deduplicate_assignments(result)

    # Mapear puntajes a los grupos
    score_map = {s["group_id"]: s for s in result.get("scores", [])}
    for group in groups:
        gid = group["group_id"]
        if gid in score_map:
            group["importance_score"] = score_map[gid].get("total_score", 0)
            group["score_breakdown"] = score_map[gid].get("score_breakdown", {})
            group["score_justification"] = score_map[gid].get("justification", "")
        else:
            group["importance_score"] = 0
            group["score_breakdown"] = {}

    # Ordenar por importancia descendente
    groups.sort(key=lambda g: g.get("importance_score", 0), reverse=True)
    print("[LLM] Evaluación de importancia completada")
    return groups


# ═══════════════════════════════════════════════════════════════════════
# PASO 4: Fusionar/consolidar grupos si se excede el límite
# ═══════════════════════════════════════════════════════════════════════

def propose_group_merges(
    groups: list[dict],
    target_count: int,
) -> list[dict]:
    """
    Usa el LLM para proponer fusiones de grupos cuando se excede MAX_GROUPS.

    Parameters
    ----------
    groups : list[dict]
        Todos los grupos funcionales actuales.
    target_count : int
        Número objetivo de grupos (debe ser < MAX_GROUPS).

    Returns
    -------
    list[dict]
        Lista de grupos funcionales después de las fusiones propuestas.
    """
    current_count = len(groups)
    if current_count <= target_count:
        print(f"[LLM] {current_count} grupos ≤ {target_count}. No se necesitan fusiones.")
        return groups

    groups_text = groups_to_text(groups)
    merges_needed = current_count - target_count

    system_prompt = """Eres un ecólogo marino experto en modelación ecosistémica ATLANTIS.
Necesitas reducir el número de grupos funcionales fusionando grupos similares.

REGLAS PARA FUSIONAR:
- Solo fusionar grupos con roles funcionales SIMILARES.
- Priorizar la fusión de grupos con bajo puntaje de importancia.
- Mantener la diversidad funcional del ecosistema.
- Asegurar que las especies fusionadas sigan teniendo sentido ecológico juntas.
- NO fusionar grupos de niveles tróficos muy diferentes.
- Responde ÚNICAMENTE con un JSON válido."""

    user_prompt = f"""## GRUPOS FUNCIONALES ACTUALES ({current_count} grupos):
{groups_text}

## NECESIDAD:
Reducir a {target_count} grupos o menos (fusionar al menos {merges_needed} pares).

## INSTRUCCIÓN:
Propón qué grupos fusionar. Para cada fusión, define el grupo resultante.

Responde con:
```json
{{
  "merges": [
    {{
      "merge_groups": ["FG_id_1", "FG_id_2"],
      "result": {{
        "group_id": "FG_id_1",
        "group_name": "Nuevo nombre del grupo fusionado",
        "description": "Nueva descripción del grupo fusionado",
        "characteristics": {{
          "habitat": "...",
          "trophic_level": "...",
          "size_class": "...",
          "taxonomic_affinity": "..."
        }}
      }},
      "reason": "Justificación de la fusión"
    }}
  ]
}}
```"""

    print(f"[LLM] Proponiendo fusiones ({current_count} → {target_count} grupos)...")
    response = _call_llm(system_prompt, user_prompt, stream=LLM_STREAMING)
    result = _extract_json_from_response(response)
    result = _deduplicate_assignments(result)

    # Aplicar fusiones
    group_map = {g["group_id"]: g for g in groups}
    removed_ids = set()

    for merge in result.get("merges", []):
        merge_ids = merge["merge_groups"]
        merged_result = merge["result"]

        # Combinar especies de todos los grupos a fusionar
        all_species = []
        for mid in merge_ids:
            if mid in group_map:
                all_species.extend(group_map[mid].get("species", []))
                if mid != merged_result["group_id"]:
                    removed_ids.add(mid)

        # Actualizar el grupo principal
        target_id = merged_result["group_id"]
        if target_id in group_map:
            group_map[target_id]["group_name"] = merged_result["group_name"]
            group_map[target_id]["description"] = merged_result["description"]
            group_map[target_id]["characteristics"] = merged_result.get(
                "characteristics", group_map[target_id].get("characteristics", {})
            )
            group_map[target_id]["species"] = list(set(all_species))

    # Remover grupos absorbidos
    merged_groups = [g for g in groups if g["group_id"] not in removed_ids]
    print(
        f"[LLM] Fusiones aplicadas: {current_count} → {len(merged_groups)} grupos"
    )
    return merged_groups
