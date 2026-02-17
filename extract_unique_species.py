#!/usr/bin/env python3
"""
extract_unique_species.py
=========================
Lee el CSV de biodiversidad filtrado por zona de estudio y genera un CSV
con la lista de especies únicas, listo para alimentar el algoritmo de
creación de grupos funcionales.

Pasos:
  1. Carga el CSV crudo de ocurrencias.
  2. Normaliza los nombres de especie (minúsculas, strip, elimina
     autoridades taxonómicas cuando es posible).
  3. Filtra registros por rango taxonómico (SPECIES por defecto).
  4. Extrae valores únicos de la columna «species».
  5. Genera  data/species_list.csv  con el formato que espera el
     pipeline (columna species_name).

Uso:
    conda activate atlantis_fg
    python extract_unique_species.py
    python extract_unique_species.py --ranks SPECIES GENUS SUBSPECIES
"""

import argparse
import re
from pathlib import Path

import pandas as pd

# ── Rutas ────────────────────────────────────────────────────────────
PROJECT_DIR = Path(__file__).parent
DATA_DIR = PROJECT_DIR / "data"

INPUT_CSV = DATA_DIR / "biodiversity_filtered_by_study_zone_20250924_094349.csv"
OUTPUT_CSV = DATA_DIR / "species_list.csv"

# Rangos taxonómicos que consideramos válidos por defecto
DEFAULT_RANKS = ["SPECIES", "GENUS", "SUBSPECIES"]


# ── Funciones ────────────────────────────────────────────────────────
def clean_species_name(name: str) -> str:
    """
    Normaliza un nombre de especie:
      - Convierte a minúsculas y elimina espacios extra.
      - Conserva solo las dos primeras palabras (género + epíteto),
        descartando autoridades taxonómicas como 'linnaeus', 'l.',
        'walker', etc.
      - Si solo hay una palabra (género), la mantiene tal cual.
    """
    name = name.strip().lower()
    # Separar en tokens
    tokens = name.split()
    if len(tokens) <= 2:
        return " ".join(tokens)
    # Heurística: si la tercera palabra parece autoridad (empieza con
    # mayúscula original, contiene punto, o es un apellido conocido),
    # nos quedamos con las dos primeras.
    third = tokens[2]
    is_authority = bool(
        re.search(r"\.", third)  # ej. "l.", "dum.cours."
        or third[0].isupper()   # ya está en minúscula, así que no aplica aquí
    )
    # Enfoque conservador: quedarnos siempre con género + epíteto
    # ya que las autoridades taxonómicas no son útiles para la
    # clasificación funcional.
    return " ".join(tokens[:2])


def extract_unique_species(
    input_csv: Path = INPUT_CSV,
    output_csv: Path = OUTPUT_CSV,
    ranks: list[str] | None = None,
) -> pd.DataFrame:
    """
    Extrae la lista de especies únicas del CSV de biodiversidad.

    Parameters
    ----------
    input_csv : Path
        Ruta al CSV de ocurrencias de biodiversidad.
    output_csv : Path
        Ruta de salida para el CSV de especies únicas.
    ranks : list[str], optional
        Rangos taxonómicos a incluir. None = todos (sin filtro).

    Returns
    -------
    pd.DataFrame
        DataFrame con columna species_name (una fila por especie única).
    """
    print(f"[Extract] Leyendo {input_csv.name}...")
    df = pd.read_csv(input_csv, usecols=["species", "taxonRank"])
    print(f"[Extract] {len(df):,} registros cargados")

    # ── Filtrar por rango taxonómico ──────────────────────────────
    if ranks:
        ranks_upper = [r.upper() for r in ranks]
        mask = df["taxonRank"].str.upper().isin(ranks_upper)
        df_filtered = df[mask].copy()
        print(
            f"[Extract] {len(df_filtered):,} registros con taxonRank "
            f"en {ranks_upper}"
        )
    else:
        df_filtered = df.copy()
        print("[Extract] Sin filtro de taxonRank (todos los registros)")

    # ── Eliminar registros sin nombre de especie ──────────────────
    df_filtered = df_filtered.dropna(subset=["species"])
    print(f"[Extract] {len(df_filtered):,} registros con nombre válido")

    # ── Normalizar nombres ────────────────────────────────────────
    df_filtered["species_clean"] = df_filtered["species"].apply(
        clean_species_name
    )

    # ── Extraer únicos ────────────────────────────────────────────
    unique_species = sorted(df_filtered["species_clean"].unique())
    print(f"[Extract] {len(unique_species):,} especies únicas extraídas")

    # ── Crear DataFrame de salida ─────────────────────────────────
    result = pd.DataFrame({"species_name": unique_species})

    # ── Guardar ───────────────────────────────────────────────────
    result.to_csv(output_csv, index=False, encoding="utf-8")
    print(f"[Extract] Guardado en {output_csv}")
    print(f"[Extract] Listo — {len(result)} especies para el algoritmo.")

    return result


# ── CLI ──────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Extrae especies únicas del CSV de biodiversidad"
    )
    parser.add_argument(
        "--ranks",
        nargs="+",
        default=DEFAULT_RANKS,
        help=(
            "Rangos taxonómicos a incluir. "
            f"Default: {DEFAULT_RANKS}. "
            "Usa --ranks ALL para incluir todos."
        ),
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Ruta al CSV de entrada (default: archivo en data/)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Ruta al CSV de salida (default: data/species_list.csv)",
    )
    args = parser.parse_args()

    input_path = Path(args.input) if args.input else INPUT_CSV
    output_path = Path(args.output) if args.output else OUTPUT_CSV

    ranks = None if args.ranks == ["ALL"] else args.ranks

    extract_unique_species(input_path, output_path, ranks)


if __name__ == "__main__":
    main()
