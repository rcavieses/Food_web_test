#!/usr/bin/env python3
"""
main.py - Main pipeline for functional group creation
==========================================================

Iterative LLM-assisted algorithm to generate an optimal configuration
of functional groups for an ATLANTIS ecosystem model
of the Gulf of California.

Uses Ollama as local LLM server (no need for cloud API keys).

Prerequisites:
  1. Install Ollama from https://ollama.ai
  2. Download a model: ollama pull mistral (or llama2, neural-chat, etc.)
  3. Run Ollama: ollama serve

Usage:
    # With LLM via Ollama (requires Ollama running):
    python main.py

    # Without LLM (heuristics only, for testing):
    python main.py --no-llm

    # With custom species file:
    python main.py --species data/my_species.csv

    # With custom initial groups:
    python main.py --groups data/my_groups.json
    
    # Specify Ollama model:
    OLLAMA_MODEL=llama2 python main.py

Author: Generated for ATLANTIS project - Gulf of California
"""

import argparse
import sys
import os
from pathlib import Path

# Add project directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import OLLAMA_API_URL, OLLAMA_MODEL, OUTPUT_DIR
from data_loader import (
    load_species_data,
    get_unique_species,
    load_existing_groups,
)
from optimizer import run_optimization


def parse_args():
    parser = argparse.ArgumentParser(
        description="Functional group optimization algorithm for ATLANTIS"
    )
    parser.add_argument(
        "--species",
        type=str,
        default=None,
        help="Path to species occurrence CSV",
    )
    parser.add_argument(
        "--groups",
        type=str,
        default=None,
        help="Path to initial functional groups JSON",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Run without LLM (heuristics only)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    use_llm = not args.no_llm

    # Check Ollama connection if using LLM
    if use_llm:
        try:
            import requests
            print(f"🔍 Checking Ollama connection at {OLLAMA_API_URL}...")
            response = requests.post(
                OLLAMA_API_URL,
                json={"model": OLLAMA_MODEL, "prompt": "test", "stream": False},
                timeout=60,
            )
            if response.status_code != 200:
                raise ConnectionError("Ollama not responding correctly")
            print(f"✅ Ollama connected. Model: {OLLAMA_MODEL}")
        except Exception as e:
            print(
                f"⚠️  Could not connect to Ollama at {OLLAMA_API_URL}\n"
                f"   Error: {e}\n"
                f"   Solutions:\n"
                f"   1. Install Ollama from https://ollama.ai\n"
                f"   2. Download model: ollama pull {OLLAMA_MODEL}\n"
                f"   3. Run Ollama: ollama serve\n"
                f"   4. Or run with --no-llm to use heuristics only\n"
            )
            response = input("Continue without LLM? (y/n): ").strip().lower()
            if response in ("s", "si", "sí", "y", "yes"):
                use_llm = False
            else:
                sys.exit(1)

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  FUNCTIONAL GROUPS ALGORITHM FOR ATLANTIS                    ║")
    print("║  Gulf of California - Ecosystem Model                        ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"\nMode: {'LLM (Ollama)' if use_llm else 'Heuristic (no LLM)'}")

    # ── Load data ───────────────────────────────────────────────
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

    # ── Final summary ──────────────────────────────────────────────
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("  ║  FINAL SUMMARY                                               ║")
    print("  ╠══════════════════════════════════════════════════════════════╣")
    print(f" ║  Functional groups: {result.n_groups:<38}║")
    print(f" ║  Assigned species: {result.assigned_species}/{result.total_species:<35}║")
    print(f" ║  Coverage: {result.coverage:<47.1%}║")
    print(f" ║  Unassigned: {len(result.unassigned_species):<47}║")
    status = "✅ MEETS" if result.meets_criteria() else "❌ DOES NOT MEET"
    print(f" ║  Status: {status:<50}║")
    print(" ╠══════════════════════════════════════════════════════════════╣")
    print(f" ║  Output files in: {str(OUTPUT_DIR):<35}║")
    print(" ║  - optimized_groups.json                                     ║")
    print(" ║  - score_report.txt                                          ║")
    print(" ║  - optimization_history.json                                 ║")
    print(" ╚══════════════════════════════════════════════════════════════╝")


if __name__ == "__main__":
    main()
