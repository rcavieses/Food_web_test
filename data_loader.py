"""
data_loader.py - Carga y preparación de datos
===============================================
Funciones para leer la base de datos de especies y los grupos funcionales existentes.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Optional

from config import SPECIES_CSV, INITIAL_GROUPS_JSON


def load_species_data(filepath: Optional[Path] = None) -> pd.DataFrame:
    """
    Carga la lista de especies únicas.

    Parameters
    ----------
    filepath : Path, optional
        Ruta al archivo CSV. Por defecto usa SPECIES_CSV de config.

    Returns
    -------
    pd.DataFrame
        DataFrame con la columna species_name.
    """
    fp = filepath or SPECIES_CSV
    df = pd.read_csv(fp)
    print(f"[DataLoader] Cargadas {len(df)} especies desde {fp.name}")
    return df


def get_unique_species(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extrae la lista de valores únicos de especie.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame con columna species_name.

    Returns
    -------
    pd.DataFrame
        DataFrame con una fila por especie única.
    """
    unique_df = df.drop_duplicates(subset="species_name").reset_index(drop=True)
    print(f"[DataLoader] {len(unique_df)} especies únicas identificadas")
    return unique_df


def load_existing_groups(filepath: Optional[Path] = None) -> list[dict]:
    """
    Carga los grupos funcionales existentes desde un archivo JSON.

    Parameters
    ----------
    filepath : Path, optional
        Ruta al archivo JSON. Por defecto usa INITIAL_GROUPS_JSON de config.

    Returns
    -------
    list[dict]
        Lista de diccionarios, cada uno representando un grupo funcional.
    """
    fp = filepath or INITIAL_GROUPS_JSON
    with open(fp, "r", encoding="utf-8") as f:
        groups = json.load(f)
    print(f"[DataLoader] Cargados {len(groups)} grupos funcionales desde {fp.name}")
    return groups


def save_groups(groups: list[dict], filepath: Path) -> None:
    """
    Guarda la lista de grupos funcionales a un archivo JSON.

    Parameters
    ----------
    groups : list[dict]
        Lista de grupos funcionales.
    filepath : Path
        Ruta de destino.
    """
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(groups, f, indent=2, ensure_ascii=False)
    print(f"[DataLoader] Guardados {len(groups)} grupos en {filepath.name}")


def species_to_text_list(species_df: pd.DataFrame) -> str:
    """
    Convierte el DataFrame de especies a un texto formateado para el LLM.

    Parameters
    ----------
    species_df : pd.DataFrame
        DataFrame de especies únicas.

    Returns
    -------
    str
        Texto con la lista de nombres científicos.
    """
    lines = []
    for _, row in species_df.iterrows():
        name = row["species_name"]
        # Incluir atributos adicionales si existen en el DataFrame
        extra_cols = [c for c in species_df.columns if c != "species_name"]
        if extra_cols:
            attrs = " | ".join(
                f"{c}: {row[c]}" for c in extra_cols if pd.notna(row[c])
            )
            lines.append(f"- {name} | {attrs}" if attrs else f"- {name}")
        else:
            lines.append(f"- {name}")
    return "\n".join(lines)


def groups_to_text(groups: list[dict]) -> str:
    """
    Convierte la lista de grupos funcionales a texto para el LLM.

    Parameters
    ----------
    groups : list[dict]
        Lista de grupos funcionales.

    Returns
    -------
    str
        Texto formateado con la información de cada grupo.
    """
    lines = []
    for g in groups:
        sp_list = ", ".join(g.get("species", [])) or "(vacío)"
        chars = g.get("characteristics", {})
        char_str = " | ".join(f"{k}: {v}" for k, v in chars.items())
        lines.append(
            f"[{g['group_id']}] {g['group_name']}\n"
            f"  Descripción: {g['description']}\n"
            f"  Características: {char_str}\n"
            f"  Especies asignadas: {sp_list}\n"
        )
    return "\n".join(lines)
