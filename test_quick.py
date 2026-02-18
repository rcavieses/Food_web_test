#!/usr/bin/env python3
"""
test_quick.py - Test rápido con un subconjunto pequeño de especies
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import OUTPUT_DIR
from data_loader import (
    load_species_data,
    get_unique_species,
    load_existing_groups,
    species_to_text_list,
    groups_to_text,
    save_groups,
)
from llm_classifier import classify_species_into_groups
from scoring import compute_quantitative_scores, generate_score_report

# Cargar datos
raw_df = load_species_data()
species_df = get_unique_species(raw_df)

# Usar solo 300 especies para testing rápido
small_species_df = species_df.iloc[:300].copy()
print(f"[TEST] Usando {len(small_species_df)} especies (de {len(species_df)} totales)\n")

initial_groups = load_existing_groups()

# Preparar texto
species_text = species_to_text_list(small_species_df)
groups_text = groups_to_text(initial_groups)

print("=" * 80)
print("CLASIFICACIÓN CON LLM (300 especies de prueba)")
print("=" * 80)

# Clasificar
groups, unassigned = classify_species_into_groups(species_text, groups_text, initial_groups.copy())

print(f"\n✅ Clasificación completada:")
print(f"   - Especies asignadas: {sum(len(g['species']) for g in groups)}")
print(f"   - Especies sin grupo: {len(unassigned)}")
print(f"   - Grupos con especies: {sum(1 for g in groups if g['species'])}")

# Mostrar resultados
print("\n" + "=" * 80)
print("GRUPOS CON ASIGNACIONES")
print("=" * 80)

for group in groups:
    if group["species"]:
        print(f"\n{group['group_id']} - {group['group_name']}")
        print(f"   Especies: {', '.join(group['species'][:5])}" + ("..." if len(group['species']) > 5 else ""))
        print(f"   Total: {len(group['species'])}")

# Guardar resultado
output_path = OUTPUT_DIR / "test_result_300sp.json"
save_groups(groups, output_path)
print(f"\n[OK] Resultado guardado en {output_path}")
