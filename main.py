#!/usr/bin/env python3
"""
main.py - Pipeline principal para la creación de grupos funcionales
====================================================================

Algoritmo iterativo asistido por LLM para generar una configuración
óptima de grupos funcionales para un modelo ecosistémico ATLANTIS
del Golfo de California.

Uso:
    # Con LLM (requiere ANTHROPIC_API_KEY):
    python main.py

    # Sin LLM (solo heurísticas, para testing):
    python main.py --no-llm

    # Con archivo de especies personalizado:
    python main.py --species datos/mis_especies.csv

    # Con grupos iniciales personalizados:
    python main.py --groups datos/mis_grupos.json

Autor: Generado para el proyecto ATLANTIS - Golfo de California
"""

import argparse
import sys
import os
from pathlib import Path

# Añadir directorio del proyecto al path
sys.path.insert(0, str(Path(__file__).parent))

from config import ANTHROPIC_API_KEY, OUTPUT_DIR
from data_loader import (
    load_species_data,
    get_unique_species,
    load_existing_groups,
)
from optimizer import run_optimization


def parse_args():
    parser = argparse.ArgumentParser(
        description="Algoritmo de optimización de grupos funcionales para ATLANTIS"
    )
    parser.add_argument(
        "--species",
        type=str,
        default=None,
        help="Ruta al CSV de ocurrencia de especies",
    )
    parser.add_argument(
        "--groups",
        type=str,
        default=None,
        help="Ruta al JSON de grupos funcionales iniciales",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Ejecutar sin LLM (solo heurísticas)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    use_llm = not args.no_llm

    # Verificar API key si se usa LLM
    if use_llm and not ANTHROPIC_API_KEY:
        print(
            "⚠️  ANTHROPIC_API_KEY no está definida.\n"
            "   Opciones:\n"
            "   1. export ANTHROPIC_API_KEY='tu-api-key'\n"
            "   2. Ejecutar con --no-llm para usar solo heurísticas\n"
        )
        # Intentar modo heurístico como fallback
        response = input("¿Deseas continuar sin LLM? (s/n): ").strip().lower()
        if response in ("s", "si", "sí", "y", "yes"):
            use_llm = False
        else:
            sys.exit(1)

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  ALGORITMO DE GRUPOS FUNCIONALES PARA ATLANTIS             ║")
    print("║  Golfo de California - Modelo Ecosistémico                 ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"\nModo: {'LLM (Claude)' if use_llm else 'Heurístico (sin LLM)'}")

    # ── Cargar datos ──────────────────────────────────────────────
    species_path = Path(args.species) if args.species else None
    groups_path = Path(args.groups) if args.groups else None

    raw_df = load_species_data(species_path)
    species_df = get_unique_species(raw_df)
    initial_groups = load_existing_groups(groups_path)

    # ── Ejecutar optimización ─────────────────────────────────────
    result = run_optimization(
        species_df=species_df,
        initial_groups=initial_groups,
        use_llm=use_llm,
    )

    # ── Resumen final ─────────────────────────────────────────────
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║  RESUMEN FINAL                                             ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║  Grupos funcionales: {result.n_groups:<38}║")
    print(f"║  Especies asignadas: {result.assigned_species}/{result.total_species:<35}║")
    print(f"║  Cobertura: {result.coverage:<47.1%}║")
    print(f"║  Sin grupo: {len(result.unassigned_species):<47}║")
    status = "✅ CUMPLE" if result.meets_criteria() else "❌ NO CUMPLE"
    print(f"║  Estado: {status:<50}║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║  Archivos de salida en: {str(OUTPUT_DIR):<35}║")
    print("║  - optimized_groups.json                                   ║")
    print("║  - score_report.txt                                        ║")
    print("║  - optimization_history.json                                ║")
    print("╚══════════════════════════════════════════════════════════════╝")


if __name__ == "__main__":
    main()
