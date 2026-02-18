"""
optimizer.py - Algoritmo iterativo de optimización de grupos funcionales
=========================================================================
Ejecuta el ciclo principal:
  1. Clasificar especies → grupos existentes
  2. Crear grupos para las no clasificadas
  3. Evaluar importancia
  4. Verificar restricción de <80 grupos
  5. Fusionar si es necesario
  6. Iterar hasta convergencia o max iteraciones
"""

import copy
import json
from pathlib import Path

import pandas as pd

from config import (
    MAX_GROUPS,
    MAX_ITERATIONS,
    TARGET_UNASSIGNED_RATIO,
    OUTPUT_DIR,
)
from data_loader import (
    species_to_text_list,
    groups_to_text,
    save_groups,
)
from llm_classifier import (
    classify_species_into_groups,
    create_groups_for_unassigned,
    evaluate_group_importance,
    propose_group_merges,
)
from scoring import (
    compute_quantitative_scores,
    compute_composite_score,
    generate_score_report,
)


class OptimizationResult:
    """Resultado de una iteración de optimización."""

    def __init__(
        self,
        iteration: int,
        groups: list[dict],
        total_species: int,
        assigned_species: int,
        unassigned_species: list[str],
    ):
        self.iteration = iteration
        self.groups = groups
        self.total_species = total_species
        self.assigned_species = assigned_species
        self.unassigned_species = unassigned_species
        self.n_groups = len(groups)
        self.coverage = assigned_species / max(total_species, 1)
        self.unassigned_ratio = len(unassigned_species) / max(total_species, 1)

    def __repr__(self):
        return (
            f"Iteración {self.iteration}: "
            f"{self.n_groups} grupos, "
            f"{self.assigned_species}/{self.total_species} especies asignadas "
            f"({self.coverage:.1%} cobertura), "
            f"{len(self.unassigned_species)} sin grupo"
        )

    def meets_criteria(self) -> bool:
        """Verifica si la solución cumple con todos los criterios."""
        return (
            self.n_groups <= MAX_GROUPS
            and self.unassigned_ratio <= TARGET_UNASSIGNED_RATIO
        )


def _count_assigned_species(groups: list[dict]) -> tuple[int, set[str]]:
    """Cuenta las especies asignadas y retorna el conjunto."""
    assigned = set()
    for g in groups:
        assigned.update(g.get("species", []))
    return len(assigned), assigned


def run_optimization(
    species_df: pd.DataFrame,
    initial_groups: list[dict],
    use_llm: bool = True,
) -> OptimizationResult:
    """
    Ejecuta el algoritmo iterativo de optimización.

    Parameters
    ----------
    species_df : pd.DataFrame
        DataFrame de especies únicas con sus atributos.
    initial_groups : list[dict]
        Grupos funcionales iniciales.
    use_llm : bool
        Si True, usa el LLM para clasificación. Si False, solo usa heurísticas.

    Returns
    -------
    OptimizationResult
        Mejor resultado encontrado.
    """
    all_species = set(species_df["species_name"].tolist())
    total_species = len(all_species)
    species_text = species_to_text_list(species_df)

    # Estado actual
    groups = copy.deepcopy(initial_groups)
    best_result = None
    history = []

    print("\n" + "=" * 80)
    print("INICIO DEL ALGORITMO DE OPTIMIZACIÓN DE GRUPOS FUNCIONALES")
    print("=" * 80)
    print(f"Especies totales: {total_species}")
    print(f"Grupos iniciales: {len(groups)}")
    print(f"Límite de grupos: {MAX_GROUPS}")
    print(f"Iteraciones máximas: {MAX_ITERATIONS}")
    print(f"Objetivo de cobertura: ≥{(1 - TARGET_UNASSIGNED_RATIO):.0%}")
    print("=" * 80 + "\n")

    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"\n{'─' * 60}")
        print(f"  ITERACIÓN {iteration}")
        print(f"{'─' * 60}")

        # ── Paso 1: Clasificar especies en grupos existentes ──────
        if use_llm:
            groups_text = groups_to_text(groups)
            groups, unassigned = classify_species_into_groups(
                species_text, groups_text, groups
            )
        else:
            groups, unassigned = _heuristic_classify(species_df, groups)

        # ── Paso 2: Crear grupos para las no clasificadas ─────────
        if unassigned and use_llm:
            new_groups = create_groups_for_unassigned(
                unassigned, species_text, groups
            )
            groups.extend(new_groups)
            # Re-verificar unassigned después de nuevos grupos
            _, assigned_set = _count_assigned_species(groups)
            unassigned = [sp for sp in all_species if sp not in assigned_set]

        # ── Paso 3: Evaluar importancia ───────────────────────────
        groups = compute_quantitative_scores(groups, species_df)
        if use_llm:
            groups = evaluate_group_importance(groups, species_df)
        groups = compute_composite_score(groups)

        # ── Paso 4: Verificar restricción de grupos ───────────────
        if len(groups) > MAX_GROUPS:
            print(f"\n⚠️  {len(groups)} grupos > {MAX_GROUPS} límite. Fusionando...")
            target = min(MAX_GROUPS - 5, len(groups) - 5)  # Dejar margen
            if use_llm:
                groups = propose_group_merges(groups, target)
            else:
                groups = _heuristic_merge(groups, target)

            # Recalcular puntajes después de fusiones
            groups = compute_quantitative_scores(groups, species_df)
            groups = compute_composite_score(groups)

        # ── Registrar resultado ───────────────────────────────────
        n_assigned, assigned_set = _count_assigned_species(groups)
        current_unassigned = [sp for sp in all_species if sp not in assigned_set]

        result = OptimizationResult(
            iteration=iteration,
            groups=copy.deepcopy(groups),
            total_species=total_species,
            assigned_species=n_assigned,
            unassigned_species=current_unassigned,
        )
        history.append(result)
        print(f"\n  📊 {result}")

        # ── Actualizar mejor resultado ────────────────────────────
        if best_result is None or (
            result.coverage >= best_result.coverage
            and result.n_groups <= MAX_GROUPS
        ):
            best_result = result

        # ── Verificar convergencia ────────────────────────────────
        if result.meets_criteria():
            print(f"\n✅ Criterios cumplidos en iteración {iteration}!")
            break

        # Verificar si mejoramos respecto a la iteración anterior
        if len(history) >= 2:
            prev = history[-2]
            if (
                abs(result.coverage - prev.coverage) < 0.01
                and result.n_groups == prev.n_groups
            ):
                print(f"\n⏹️  Convergencia alcanzada (sin mejora significativa).")
                break

    # ── Reporte final ─────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("RESULTADO FINAL DE OPTIMIZACIÓN")
    print("=" * 80)
    print(f"Mejor resultado: {best_result}")
    print(f"Criterios {'✅ CUMPLIDOS' if best_result.meets_criteria() else '❌ NO CUMPLIDOS'}")

    if best_result.unassigned_species:
        print(f"\nEspecies sin grupo ({len(best_result.unassigned_species)}):")
        for sp in best_result.unassigned_species:
            print(f"  - {sp}")

    # Guardar resultado
    report = generate_score_report(best_result.groups)
    print(f"\n{report}")

    # Guardar archivos de salida
    save_groups(best_result.groups, OUTPUT_DIR / "optimized_groups.json")

    report_path = OUTPUT_DIR / "score_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n[Output] Reporte guardado en {report_path}")

    # Guardar historial
    history_data = [
        {
            "iteration": r.iteration,
            "n_groups": r.n_groups,
            "assigned": r.assigned_species,
            "total": r.total_species,
            "coverage": r.coverage,
            "unassigned_count": len(r.unassigned_species),
        }
        for r in history
    ]
    history_path = OUTPUT_DIR / "optimization_history.json"
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history_data, f, indent=2)

    return best_result


# ═══════════════════════════════════════════════════════════════════════
# Alternativas heurísticas (sin LLM) para pruebas
# ═══════════════════════════════════════════════════════════════════════

def _heuristic_classify(
    species_df: pd.DataFrame,
    groups: list[dict],
) -> tuple[list[dict], list[str]]:
    """
    Clasificación heurística basada en coincidencia de atributos.
    Útil para testing sin conexión a la API.

    Si el DataFrame solo tiene species_name (sin atributos ecológicos),
    todas las especies quedan como no asignadas — lo cual fuerza al
    modo LLM a crearlas.
    """
    unassigned = []
    has_attrs = any(
        c in species_df.columns
        for c in ("habitat", "trophic_level", "order", "family")
    )

    for _, row in species_df.iterrows():
        sp_name = row["species_name"]

        if not has_attrs:
            # Sin atributos ecológicos no podemos clasificar heurísticamente
            unassigned.append(sp_name)
            continue

        best_match = None
        best_score = -1

        for group in groups:
            chars = group.get("characteristics", {})
            score = 0
            if chars.get("habitat") == row.get("habitat"):
                score += 3
            if chars.get("trophic_level") == row.get("trophic_level"):
                score += 3
            if str(row.get("order", "")) in chars.get("taxonomic_affinity", ""):
                score += 2
            if str(row.get("family", "")) in chars.get("taxonomic_affinity", ""):
                score += 2

            if score > best_score:
                best_score = score
                best_match = group

        if best_match and best_score >= 4:
            if sp_name not in best_match["species"]:
                best_match["species"].append(sp_name)
        else:
            unassigned.append(sp_name)

    assigned = sum(len(g["species"]) for g in groups)
    print(
        f"[Heuristic] Clasificación: {assigned} asignadas, "
        f"{len(unassigned)} sin grupo"
    )
    return groups, unassigned


def _heuristic_merge(groups: list[dict], target_count: int) -> list[dict]:
    """
    Fusión heurística basada en similitud de características.
    Fusiona los grupos con menor puntaje compuesto.
    """
    # Ordenar por puntaje ascendente (los menos importantes primero)
    sorted_groups = sorted(groups, key=lambda g: g.get("composite_score", 0))

    while len(sorted_groups) > target_count and len(sorted_groups) > 1:
        # Tomar los dos grupos menos importantes
        g1 = sorted_groups.pop(0)
        g2 = sorted_groups.pop(0)

        # Fusionar
        merged = {
            "group_id": g1["group_id"],
            "group_name": f"{g1['group_name']} / {g2['group_name']}",
            "description": f"Grupo fusionado: {g1['description']} + {g2['description']}",
            "characteristics": g1.get("characteristics", {}),
            "species": list(set(g1.get("species", []) + g2.get("species", []))),
            "composite_score": max(
                g1.get("composite_score", 0), g2.get("composite_score", 0)
            ),
        }
        sorted_groups.append(merged)

    print(f"[Heuristic] Fusión completada: {len(groups)} → {len(sorted_groups)} grupos")
    return sorted_groups
