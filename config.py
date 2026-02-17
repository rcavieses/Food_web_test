"""
config.py - Configuración del proyecto de Grupos Funcionales
=============================================================
Parámetros globales, rutas de archivos y criterios de evaluación.
"""

import os
from pathlib import Path

# ─── Rutas del proyecto ───────────────────────────────────────────────
PROJECT_DIR = Path(__file__).parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = PROJECT_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

SPECIES_CSV = DATA_DIR / "species_occurrences.csv"
INITIAL_GROUPS_JSON = DATA_DIR / "initial_groups.json"

# ─── Restricciones del algoritmo ──────────────────────────────────────
MAX_GROUPS = 80                # Límite máximo de grupos funcionales
MAX_ITERATIONS = 10            # Iteraciones máximas del optimizador
MIN_SPECIES_PER_GROUP = 1      # Mínimo de especies para considerar un grupo válido
TARGET_UNASSIGNED_RATIO = 0.05 # Objetivo: <5% de especies sin grupo

# ─── Configuración del LLM ───────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
LLM_MODEL = "claude-sonnet-4-20250514"
LLM_MAX_TOKENS = 4096
LLM_TEMPERATURE = 0.3  # Baja temperatura para consistencia en clasificación

# ─── Criterios de puntaje para importancia de grupos ──────────────────
# Cada criterio tiene un peso (weight) y una descripción.
# El puntaje total de un grupo = suma ponderada de todos los criterios.
SCORING_CRITERIA = {
    "species_richness": {
        "weight": 0.20,
        "description": "Número de especies en el grupo (normalizado)",
    },
    "trophic_importance": {
        "weight": 0.20,
        "description": "Rol trófico clave en la red alimentaria del ecosistema",
    },
    "commercial_value": {
        "weight": 0.15,
        "description": "Importancia pesquera/comercial de las especies del grupo",
    },
    "ecological_role": {
        "weight": 0.20,
        "description": "Función ecosistémica (e.g., bioingeniería, bioturbación, producción primaria)",
    },
    "conservation_status": {
        "weight": 0.10,
        "description": "Presencia de especies protegidas o en peligro",
    },
    "uniqueness": {
        "weight": 0.15,
        "description": "Qué tan único es el nicho funcional (baja redundancia con otros grupos)",
    },
}

# ─── Mapeo de valores textuales a puntajes numéricos ──────────────────
COMMERCIAL_IMPORTANCE_MAP = {
    "high": 1.0,
    "medium": 0.6,
    "low": 0.3,
    "protected": 0.8,  # Alto valor de conservación
    "ecological": 0.7, # Alto valor ecológico
}

TROPHIC_IMPORTANCE_MAP = {
    "primary_producer": 1.0,
    "filter_feeder": 0.9,
    "herbivore": 0.8,
    "detritivore": 0.7,
    "planktivore": 0.9,
    "omnivore": 0.6,
    "carnivore": 0.7,
    "mixotroph": 0.8,
}
