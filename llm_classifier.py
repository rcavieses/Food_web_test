"""
llm_classifier.py - Interfaz con el LLM para clasificación de especies
========================================================================
Usa la API de Anthropic para:
  1. Asignar especies a grupos funcionales existentes.
  2. Crear nuevos grupos para especies no clasificadas.
  3. Proponer fusiones de grupos cuando se excede el límite.
"""

import json
import re
from typing import Optional

from anthropic import Anthropic

from config import (
    ANTHROPIC_API_KEY,
    LLM_MODEL,
    LLM_MAX_TOKENS,
    LLM_TEMPERATURE,
    MAX_GROUPS,
    SCORING_CRITERIA,
)
from data_loader import species_to_text_list, groups_to_text


def _get_client() -> Anthropic:
    """Crea el cliente de la API de Anthropic."""
    if not ANTHROPIC_API_KEY:
        raise ValueError(
            "No se encontró ANTHROPIC_API_KEY. "
            "Define la variable de entorno antes de ejecutar."
        )
    return Anthropic(api_key=ANTHROPIC_API_KEY)


def _call_llm(system_prompt: str, user_prompt: str) -> str:
    """
    Llamada genérica al LLM.

    Parameters
    ----------
    system_prompt : str
        Instrucciones del sistema.
    user_prompt : str
        Mensaje del usuario.

    Returns
    -------
    str
        Respuesta del modelo.
    """
    client = _get_client()
    message = client.messages.create(
        model=LLM_MODEL,
        max_tokens=LLM_MAX_TOKENS,
        temperature=LLM_TEMPERATURE,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text


def _extract_json_from_response(response: str) -> dict | list:
    """
    Extrae JSON de la respuesta del LLM, manejando posibles bloques de código.
    Maneja JSON incompleto intentando cerrarlo automáticamente.

    Parameters
    ----------
    response : str
        Texto crudo de la respuesta del LLM.

    Returns
    -------
    dict | list
        Objeto JSON parseado.
    """
    # Intentar extraer de un bloque ```json ... ```
    json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
    if json_match:
        extracted = json_match.group(1)
        try:
            return json.loads(extracted)
        except json.JSONDecodeError:
            # Intentar cerrar incompletos
            try:
                incomplete = extracted.rstrip()
                if incomplete.endswith(","):
                    incomplete = incomplete[:-1]
                if incomplete.startswith("["):
                    return json.loads(incomplete + "]")
                elif incomplete.startswith("{"):
                    return json.loads(incomplete + "}")
            except json.JSONDecodeError:
                pass

    # Intentar extraer de un bloque ``` ... ```
    code_match = re.search(r"```\s*(.*?)\s*```", response, re.DOTALL)
    if code_match:
        extracted = code_match.group(1)
        try:
            return json.loads(extracted)
        except json.JSONDecodeError:
            try:
                incomplete = extracted.rstrip()
                if incomplete.endswith(","):
                    incomplete = incomplete[:-1]
                if incomplete.startswith("["):
                    return json.loads(incomplete + "]")
                elif incomplete.startswith("{"):
                    return json.loads(incomplete + "}")
            except json.JSONDecodeError:
                pass

    # Intentar parsear directamente (buscar primer [ o {)
    for i, char in enumerate(response):
        if char in ("[", "{"):
            try:
                return json.loads(response[i:])
            except json.JSONDecodeError:
                # Intentar cerrar incompleto
                try:
                    incomplete = response[i:].rstrip()
                    if incomplete.endswith(","):
                        incomplete = incomplete[:-1]
                    closing = "]" if char == "[" else "}"
                    return json.loads(incomplete + closing)
                except json.JSONDecodeError:
                    continue

    raise ValueError(f"No se pudo extraer JSON de la respuesta:\n{response[:500]}")


# ═══════════════════════════════════════════════════════════════════════
# PASO 1: Asignar especies a grupos existentes
# ═══════════════════════════════════════════════════════════════════════

BATCH_SIZE = 250  # Especies por llamada al LLM (balance entre eficiencia y confiabilidad)


def classify_species_into_groups(
    species_text: str,
    groups_text: str,
    groups: list[dict],
) -> tuple[list[dict], list[str]]:
    """
    Usa el LLM para asignar cada especie a un grupo funcional existente.
    Procesa en lotes de BATCH_SIZE especies para respetar los límites del LLM.

    Parameters
    ----------
    species_text : str
        Lista de especies formateada como texto.
    groups_text : str
        Lista de grupos funcionales formateada como texto.
    groups : list[dict]
        Grupos funcionales actuales (se modifican in-place las listas de especies).

    Returns
    -------
    tuple[list[dict], list[str]]
        - Grupos actualizados con especies asignadas.
        - Lista de nombres de especies que no pudieron ser asignadas.
    """
    # Separar la lista de especies en líneas individuales
    species_lines = [l for l in species_text.strip().split("\n") if l.strip()]
    total = len(species_lines)

    # Dividir en lotes
    batches = [
        species_lines[i : i + BATCH_SIZE]
        for i in range(0, total, BATCH_SIZE)
    ]
    n_batches = len(batches)
    print(f"[LLM] Clasificando {total} especies en {n_batches} lotes de ~{BATCH_SIZE}...")

    system_prompt = """Eres un ecólogo marino experto en modelación de ecosistemas.
Tu tarea es asignar especies a grupos funcionales existentes basándote en sus
características ecológicas y funcionales.

REGLAS:
- Cada especie debe asignarse al grupo que mejor represente su rol funcional.
- Si una especie NO encaja razonablemente en ningún grupo existente, márcala como "sin_grupo".
- Prioriza el rol trófico y el hábitat sobre la taxonomía.
- Responde ÚNICAMENTE con un JSON válido, sin texto adicional."""

    group_map = {g["group_id"]: i for i, g in enumerate(groups)}
    all_unassigned = []

    for batch_idx, batch in enumerate(batches, 1):
        batch_text = "\n".join(batch)
        user_prompt = f"""## GRUPOS FUNCIONALES ACTUALES:
{groups_text}

## LISTA DE ESPECIES A CLASIFICAR (lote {batch_idx}/{n_batches}):
{batch_text}

## INSTRUCCIÓN:
Asigna cada especie al group_id del grupo funcional más apropiado.
Si no encaja en ninguno, usa "sin_grupo".

Responde con un JSON con esta estructura:
```json
{{
  "assignments": [
    {{"species": "nombre cientifico", "group_id": "FG01", "reason": "breve justificación"}},
    {{"species": "otra especie", "group_id": "sin_grupo", "reason": "motivo"}}
  ]
}}
```"""

        print(f"  [Lote {batch_idx}/{n_batches}] Procesando {len(batch)} especies...")
        response = _call_llm(system_prompt, user_prompt)
        result = _extract_json_from_response(response)

        for assignment in result.get("assignments", []):
            sp = assignment["species"]
            gid = assignment["group_id"]

            if gid == "sin_grupo" or gid not in group_map:
                all_unassigned.append(sp)
            else:
                idx = group_map[gid]
                if sp not in groups[idx]["species"]:
                    groups[idx]["species"].append(sp)

        assigned_so_far = sum(len(g["species"]) for g in groups)
        print(f"  [Lote {batch_idx}/{n_batches}] Acumulado: {assigned_so_far} asignadas, {len(all_unassigned)} sin grupo")

    print(
        f"[LLM] Clasificación completada: "
        f"{sum(len(g['species']) for g in groups)} asignadas, "
        f"{len(all_unassigned)} sin grupo"
    )
    return groups, all_unassigned


# ═══════════════════════════════════════════════════════════════════════
# PASO 2: Crear nuevos grupos para especies sin clasificar
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

    system_prompt = """Eres un ecólogo marino experto en modelación de ecosistemas.
Tu tarea es crear NUEVOS grupos funcionales para especies que no encajan en los grupos existentes.

REGLAS:
- Cada grupo debe representar un ROL FUNCIONAL específico en el ecosistema.
- Agrupa especies por similitud funcional (hábitat + nivel trófico + rol ecológico).
- Evita crear grupos redundantes con los existentes.
- Minimiza el número de grupos nuevos agrupando especies cuando sea ecológicamente válido.
- No crees más de 40 grupos nuevos por lote.
- Responde ÚNICAMENTE con un JSON válido, sin texto adicional."""

    # Procesar en lotes
    batches = [
        unassigned_species[i : i + BATCH_SIZE]
        for i in range(0, len(unassigned_species), BATCH_SIZE)
    ]
    n_batches = len(batches)
    print(
        f"[LLM] Creando grupos para {len(unassigned_species)} especies "
        f"sin clasificar ({n_batches} lotes)..."
    )

    all_new_groups = []

    for batch_idx, batch in enumerate(batches, 1):
        unassigned_str = "\n".join(f"- {sp}" for sp in batch)
        current_next_id = next_id + len(all_new_groups)

        user_prompt = f"""## ESPECIES SIN GRUPO ASIGNADO (lote {batch_idx}/{n_batches}):
{unassigned_str}

## GRUPOS YA EXISTENTES (para evitar redundancias):
{', '.join(existing_names + [g['group_name'] for g in all_new_groups])}

## INSTRUCCIÓN:
Crea los grupos funcionales necesarios para clasificar estas especies.
Comienza los IDs desde FG{current_next_id:02d}.

Responde con un JSON con esta estructura:
```json
{{
  "new_groups": [
    {{
      "group_id": "FG{current_next_id:02d}",
      "group_name": "Nombre descriptivo del grupo",
      "description": "Descripción del rol funcional en el ecosistema",
      "characteristics": {{
        "habitat": "benthic/pelagic/demersal/coastal/terrestrial",
        "trophic_level": "carnivore/herbivore/omnivore/etc.",
        "size_class": "small/medium/large",
        "taxonomic_affinity": "grupo taxonómico principal"
      }},
      "species": ["especie1", "especie2"]
    }}
  ]
}}
```"""

        print(f"  [Lote {batch_idx}/{n_batches}] Creando grupos para {len(batch)} especies...")
        response = _call_llm(system_prompt, user_prompt)
        result = _extract_json_from_response(response)

        new_groups = result.get("new_groups", [])
        all_new_groups.extend(new_groups)
        print(f"  [Lote {batch_idx}/{n_batches}] {len(new_groups)} grupos nuevos (total acumulado: {len(all_new_groups)})")

    print(f"[LLM] Se crearon {len(all_new_groups)} nuevos grupos funcionales en total")
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
    response = _call_llm(system_prompt, user_prompt)
    result = _extract_json_from_response(response)

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
    response = _call_llm(system_prompt, user_prompt)
    result = _extract_json_from_response(response)

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
