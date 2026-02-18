"""
Visualización de los grupos funcionales y el número de especies en cada uno
"""
import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Cargar los datos
output_dir = Path(__file__).parent / "output"
groups_file = output_dir / "optimized_groups.json"

with open(groups_file, 'r', encoding='utf-8') as f:
    groups = json.load(f)

# Extraer información
group_names = [group['group_name'] for group in groups]
species_counts = [len(group['species']) for group in groups]
total_groups = len(groups)
total_species = sum(species_counts)

print(f"{'='*60}")
print(f"RESUMEN DE GRUPOS FUNCIONALES")
print(f"{'='*60}")
print(f"Total de grupos: {total_groups}")
print(f"Total de especies: {total_species}")
print(f"Promedio de especies por grupo: {total_species / total_groups:.1f}")
print(f"Grupo más grande: {group_names[species_counts.index(max(species_counts))]} ({max(species_counts)} especies)")
print(f"Grupo más pequeño: {group_names[species_counts.index(min(species_counts))]} ({min(species_counts)} especies)")
print(f"{'='*60}\n")

# Crear figura con dos subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

# Gráfico 1: Barras horizontales con nombres de grupos
colors = plt.cm.tab20c(np.linspace(0, 1, len(groups)))
y_pos = np.arange(len(group_names))

bars = ax1.barh(y_pos, species_counts, color=colors)
ax1.set_yticks(y_pos)
ax1.set_yticklabels(group_names, fontsize=9)
ax1.set_xlabel('Número de especies', fontsize=11, fontweight='bold')
ax1.set_title(f'Especies por Grupo Funcional\n(Total: {total_groups} grupos, {total_species} especies)', 
              fontsize=12, fontweight='bold')
ax1.grid(axis='x', alpha=0.3)

# Añadir valores en las barras
for i, (bar, count) in enumerate(zip(bars, species_counts)):
    ax1.text(count + 0.5, bar.get_y() + bar.get_height()/2, 
             str(count), va='center', fontsize=8)

# Gráfico 2: Estadísticas resumidas
ax2.axis('off')

# Crear tabla de estadísticas
stats_text = f"""
ESTADÍSTICAS GENERALES

Total de Grupos: {total_groups}
Total de Especies: {total_species}

DISTRIBUCIÓN DE ESPECIES:
• Promedio: {total_species / total_groups:.1f} por grupo
• Máximo: {max(species_counts)} especies
• Mínimo: {min(species_counts)} especies
• Desv. Estándar: {np.std(species_counts):.1f}

TOP 10 GRUPOS GRANDES:
"""

# Ordenar grupos por número de especies
sorted_indices = np.argsort(species_counts)[::-1]
for i in range(min(10, len(groups))):
    idx = sorted_indices[i]
    stats_text += f"{i+1}. {group_names[idx]}: {species_counts[idx]} especies\n"

stats_text += f"\nTOP 10 GRUPOS PEQUEÑOS:\n"
sorted_indices_small = np.argsort(species_counts)
for i in range(min(10, len(groups))):
    idx = sorted_indices_small[i]
    stats_text += f"{i+1}. {group_names[idx]}: {species_counts[idx]} especies\n"

ax2.text(0.1, 0.95, stats_text, transform=ax2.transAxes, 
         fontsize=10, verticalalignment='top', fontfamily='monospace',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

plt.tight_layout()
plt.savefig(output_dir / 'grupos_visualization.png', dpi=300, bbox_inches='tight')
print(f"Gráfico guardado en: {output_dir / 'grupos_visualization.png'}")
plt.close()

# Crear un segundo gráfico mostrando distribución
fig, ax = plt.subplots(figsize=(12, 6))

# Histograma de distribución
ax.hist(species_counts, bins=15, color='steelblue', edgecolor='black', alpha=0.7)
ax.axvline(np.mean(species_counts), color='red', linestyle='--', linewidth=2, label=f'Media: {np.mean(species_counts):.1f}')
ax.axvline(np.median(species_counts), color='green', linestyle='--', linewidth=2, label=f'Mediana: {np.median(species_counts):.1f}')

ax.set_xlabel('Número de especies por grupo', fontsize=11, fontweight='bold')
ax.set_ylabel('Frecuencia (número de grupos)', fontsize=11, fontweight='bold')
ax.set_title('Distribución de Especies por Grupo', fontsize=12, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / 'distribucion_especies.png', dpi=300, bbox_inches='tight')
print(f"Gráfico de distribución guardado en: {output_dir / 'distribucion_especies.png'}")
plt.close()

# Crear un reporte detallado
report_path = output_dir / 'grupos_report.txt'
with open(report_path, 'w', encoding='utf-8') as f:
    f.write("="*80 + "\n")
    f.write("REPORTE DETALLADO DE GRUPOS FUNCIONALES\n")
    f.write("="*80 + "\n\n")
    
    f.write(f"RESUMEN GENERAL:\n")
    f.write(f"- Total de grupos: {total_groups}\n")
    f.write(f"- Total de especies: {total_species}\n")
    f.write(f"- Promedio de especies por grupo: {total_species / total_groups:.1f}\n")
    f.write(f"- Desviación estándar: {np.std(species_counts):.1f}\n")
    f.write(f"- Grupo más grande: {max(species_counts)} especies\n")
    f.write(f"- Grupo más pequeño: {min(species_counts)} especies\n\n")
    
    f.write("="*80 + "\n")
    f.write("LISTADO COMPLETO DE GRUPOS\n")
    f.write("="*80 + "\n\n")
    
    for idx, group in enumerate(groups, 1):
        f.write(f"{idx}. {group['group_name']} (ID: {group['group_id']})\n")
        f.write(f"   Descripción: {group['description']}\n")
        f.write(f"   Número de especies: {len(group['species'])}\n")
        f.write(f"   Especies: {', '.join(group['species'][:5])}")
        if len(group['species']) > 5:
            f.write(f", ... (+{len(group['species']) - 5} más)")
        f.write("\n\n")

print(f"Reporte guardado en: {report_path}")
