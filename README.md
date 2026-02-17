# 🐟 Algoritmo de Grupos Funcionales para ATLANTIS

**Algoritmo iterativo asistido por LLM para la creación y optimización de grupos funcionales en modelos ecosistémicos ATLANTIS.**

> Diseñado para el modelado del ecosistema del Golfo de California.

---

## Descripción

Este sistema automatiza la clasificación de especies marinas en **grupos funcionales** utilizando un modelo de lenguaje (Claude de Anthropic) como motor de razonamiento ecológico. El algoritmo itera sobre las asignaciones hasta encontrar una configuración que:

- ✅ Maximice la inclusión de especies (mínimo sin grupo)
- ✅ Mantenga la diversidad representativa del ecosistema
- ✅ Cumpla con la restricción de **< 80 grupos**
- ✅ Jerarquice los grupos por importancia ecosistémica

## Arquitectura

```
main.py                    ← Pipeline principal
├── config.py              ← Configuración y parámetros
├── data_loader.py         ← Carga de datos (CSV/JSON)
├── llm_classifier.py      ← Interfaz con Claude API
│   ├── classify_species_into_groups()
│   ├── create_groups_for_unassigned()
│   ├── evaluate_group_importance()
│   └── propose_group_merges()
├── scoring.py             ← Sistema de puntaje
│   ├── compute_quantitative_scores()
│   ├── compute_composite_score()
│   └── generate_score_report()
└── optimizer.py           ← Bucle iterativo de optimización
    └── run_optimization()
```

## Flujo del Algoritmo

```
┌─────────────────────────────────────────────────┐
│  1. Cargar especies y grupos existentes         │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│  2. LLM clasifica especies → grupos existentes  │◄─────┐
└──────────────────────┬──────────────────────────┘      │
                       ▼                                  │
┌─────────────────────────────────────────────────┐      │
│  3. LLM crea grupos para especies sin asignar   │      │
└──────────────────────┬──────────────────────────┘      │
                       ▼                                  │
┌─────────────────────────────────────────────────┐      │
│  4. Evaluar importancia (cuantitativa + LLM)    │      │
└──────────────────────┬──────────────────────────┘      │
                       ▼                                  │
┌─────────────────────────────────────────────────┐      │
│  5. ¿Grupos > 80?  → Fusionar/consolidar        │      │
└──────────────────────┬──────────────────────────┘      │
                       ▼                                  │
┌─────────────────────────────────────────────────┐      │
│  6. ¿Cobertura ≥ 95% y Grupos ≤ 80?            │      │
│     → SÍ: Fin ✅                                │      │
│     → NO: Iterar ───────────────────────────────┼──────┘
└─────────────────────────────────────────────────┘
```

## Instalación

```bash
pip install anthropic pandas
```

## Uso

### Con LLM (requiere API key de Anthropic)

```bash
export ANTHROPIC_API_KEY='tu-api-key-aqui'
python main.py
```

### Sin LLM (modo heurístico para testing)

```bash
python main.py --no-llm
```

### Con archivos personalizados

```bash
python main.py --species data/mis_especies.csv --groups data/mis_grupos.json
```

## Formato de Datos

### CSV de especies (`data/species_occurrences.csv`)

| Columna | Descripción |
|---------|-------------|
| `species_name` | Nombre científico |
| `phylum` | Phylum taxonómico |
| `class` | Clase taxonómica |
| `order` | Orden taxonómico |
| `family` | Familia taxonómica |
| `habitat` | pelagic / benthic / demersal / coastal |
| `trophic_level` | carnivore / herbivore / omnivore / planktivore / filter_feeder / detritivore / primary_producer / mixotroph |
| `depth_range_m` | Rango de profundidad (e.g., "0-200") |
| `body_size_cm` | Tamaño corporal en cm |
| `commercial_importance` | high / medium / low / protected / ecological |

### JSON de grupos funcionales (`data/initial_groups.json`)

```json
[
  {
    "group_id": "FG01",
    "group_name": "Nombre del grupo",
    "description": "Descripción del rol funcional",
    "characteristics": {
      "habitat": "pelagic",
      "trophic_level": "planktivore",
      "size_class": "small",
      "taxonomic_affinity": "Clupeiformes"
    },
    "species": []
  }
]
```

## Criterios de Puntaje

| Criterio | Peso | Descripción |
|----------|------|-------------|
| Riqueza de especies | 20% | Número de especies en el grupo |
| Importancia trófica | 20% | Rol clave en la red alimentaria |
| Valor comercial | 15% | Importancia pesquera |
| Rol ecológico | 20% | Función ecosistémica |
| Estado de conservación | 10% | Presencia de especies protegidas |
| Unicidad | 15% | Singularidad del nicho funcional |

## Salidas

El algoritmo genera tres archivos en `output/`:

- **`optimized_groups.json`** — Configuración final de grupos funcionales con especies asignadas y puntajes
- **`score_report.txt`** — Reporte tabular de ranking de grupos por importancia
- **`optimization_history.json`** — Historial de métricas por iteración

## Configuración

Editar `config.py` para ajustar:

- `MAX_GROUPS = 80` — Límite máximo de grupos
- `MAX_ITERATIONS = 10` — Iteraciones del optimizador
- `TARGET_UNASSIGNED_RATIO = 0.05` — Objetivo de cobertura (95%)
- `LLM_TEMPERATURE = 0.3` — Temperatura del LLM
- `SCORING_CRITERIA` — Pesos de los criterios de evaluación

## Notas

- El modo LLM usa **Claude Sonnet 4** para clasificación consistente y eficiente
- El modo heurístico funciona sin API key, útil para testing y ajuste de parámetros
- Los datos de ejemplo incluyen ~60 especies del Golfo de California
- El algoritmo converge típicamente en 2-4 iteraciones
