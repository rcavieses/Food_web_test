"""
scoring.py - Sistema de evaluación de importancia de grupos funcionales
========================================================================
Combina métricas cuantitativas (basadas en datos) con evaluaciones
cualitativas del LLM para asignar puntajes de importancia.
"""

import pandas as pd
from config import (
    SCORING_CRITERIA,
    COMMERCIAL_IMPORTANCE_MAP,
    TROPHIC_IMPORTANCE_MAP,
)


def compute_quantitative_scores(
    groups: list[dict],
    species_df: pd.DataFrame,
) -> list[dict]:
    """
    Calcula métricas cuantitativas para cada grupo basándose en los datos.

    Este método complementa la evaluación del LLM con datos concretos.

    Parameters
    ----------
    groups : list[dict]
        Lista de grupos funcionales con sus especies asignadas.
    species_df : pd.DataFrame
        DataFrame de especies con sus atributos.

    Returns
    -------
    list[dict]
        Grupos con campo 'quantitative_metrics' añadido.
    """
    total_species = len(species_df)
    species_data = species_df.set_index("species_name")

    for group in groups:
        sp_list = group.get("species", [])
        n_species = len(sp_list)

        metrics = {}

        # 1. Riqueza de especies (normalizada)
        metrics["species_richness"] = min(n_species / max(total_species * 0.1, 1), 1.0)

        if n_species == 0:
            metrics["avg_commercial_value"] = 0
            metrics["avg_trophic_importance"] = 0
            metrics["has_protected_species"] = 0
            metrics["depth_range_span"] = 0
            group["quantitative_metrics"] = metrics
            continue

        # 2. Valor comercial promedio
        commercial_values = []
        for sp in sp_list:
            if sp in species_data.index:
                ci = species_data.loc[sp, "commercial_importance"]
                commercial_values.append(COMMERCIAL_IMPORTANCE_MAP.get(ci, 0.5))
        metrics["avg_commercial_value"] = (
            sum(commercial_values) / len(commercial_values) if commercial_values else 0
        )

        # 3. Importancia trófica promedio
        trophic_values = []
        for sp in sp_list:
            if sp in species_data.index:
                tl = species_data.loc[sp, "trophic_level"]
                trophic_values.append(TROPHIC_IMPORTANCE_MAP.get(tl, 0.5))
        metrics["avg_trophic_importance"] = (
            sum(trophic_values) / len(trophic_values) if trophic_values else 0
        )

        # 4. Presencia de especies protegidas
        protected = 0
        for sp in sp_list:
            if sp in species_data.index:
                if species_data.loc[sp, "commercial_importance"] == "protected":
                    protected += 1
        metrics["has_protected_species"] = min(protected / max(n_species, 1), 1.0)

        # 5. Rango de profundidad (diversidad de hábitat)
        depths = []
        for sp in sp_list:
            if sp in species_data.index:
                depth_str = str(species_data.loc[sp, "depth_range_m"])
                parts = depth_str.split("-")
                if len(parts) == 2:
                    try:
                        depths.append(float(parts[1]) - float(parts[0]))
                    except ValueError:
                        pass
        metrics["depth_range_span"] = (
            min(max(depths) / 2000, 1.0) if depths else 0
        )

        group["quantitative_metrics"] = metrics

    return groups


def compute_composite_score(groups: list[dict]) -> list[dict]:
    """
    Calcula un puntaje compuesto combinando métricas cuantitativas y del LLM.

    Si el LLM ya proporcionó scores (importance_score), combina 50/50 con
    los cuantitativos. Si no, usa solo los cuantitativos.

    Parameters
    ----------
    groups : list[dict]
        Grupos con 'quantitative_metrics' y opcionalmente 'importance_score'.

    Returns
    -------
    list[dict]
        Grupos con 'composite_score' añadido y ordenados descendentemente.
    """
    for group in groups:
        qm = group.get("quantitative_metrics", {})

        # Puntaje cuantitativo ponderado
        q_score = (
            qm.get("species_richness", 0) * SCORING_CRITERIA["species_richness"]["weight"]
            + qm.get("avg_trophic_importance", 0) * SCORING_CRITERIA["trophic_importance"]["weight"]
            + qm.get("avg_commercial_value", 0) * SCORING_CRITERIA["commercial_value"]["weight"]
            + qm.get("has_protected_species", 0) * SCORING_CRITERIA["conservation_status"]["weight"]
            + qm.get("depth_range_span", 0) * SCORING_CRITERIA["uniqueness"]["weight"]
        )

        llm_score = group.get("importance_score", None)

        if llm_score is not None:
            # Combinar 50% cuantitativo + 50% LLM
            group["composite_score"] = 0.5 * q_score + 0.5 * llm_score
        else:
            group["composite_score"] = q_score

    # Ordenar
    groups.sort(key=lambda g: g.get("composite_score", 0), reverse=True)
    return groups


def generate_score_report(groups: list[dict]) -> str:
    """
    Genera un reporte textual de los puntajes de todos los grupos.

    Parameters
    ----------
    groups : list[dict]
        Grupos con puntajes calculados.

    Returns
    -------
    str
        Reporte formateado.
    """
    lines = [
        "=" * 80,
        "REPORTE DE PUNTAJES DE GRUPOS FUNCIONALES",
        "=" * 80,
        f"{'Rank':<5} {'ID':<6} {'Nombre':<45} {'#Sp':<5} {'Score':<8}",
        "-" * 80,
    ]

    for rank, group in enumerate(groups, 1):
        lines.append(
            f"{rank:<5} {group['group_id']:<6} "
            f"{group['group_name'][:44]:<45} "
            f"{len(group.get('species', [])):<5} "
            f"{group.get('composite_score', 0):.3f}"
        )

    lines.append("-" * 80)

    # Estadísticas generales
    total_sp = sum(len(g.get("species", [])) for g in groups)
    lines.append(f"\nTotal de grupos: {len(groups)}")
    lines.append(f"Total de especies asignadas: {total_sp}")
    lines.append(
        f"Puntaje promedio: "
        f"{sum(g.get('composite_score', 0) for g in groups) / max(len(groups), 1):.3f}"
    )

    return "\n".join(lines)
