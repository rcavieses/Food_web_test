"""
deduplicate_species.py - Remove duplicates from species list
============================================================
Detects and removes duplicate species from the species_list.csv file
while preserving the original order.
"""

import pandas as pd
from pathlib import Path

def deduplicate_species_list(input_file: str = "data/species_list.csv", 
                             output_file: str = "data/species_list_deduplicated.csv"):
    """Remove duplicate species from CSV file."""
    
    print("🔍 Analyzing species list for duplicates...")
    
    # Load CSV
    df = pd.read_csv(input_file, dtype=str)
    
    # Get basic stats
    total_rows = len(df)
    species_col = df.columns[0]  # First column
    
    print(f"\n📊 Initial stats:")
    print(f"   Total rows: {total_rows}")
    print(f"   Unique species: {df[species_col].nunique()}")
    print(f"   Duplicates: {total_rows - df[species_col].nunique()}")
    
    # Find duplicates
    duplicates = df[df[species_col].duplicated(keep='first')]
    if len(duplicates) > 0:
        print(f"\n⚠️  Found {len(duplicates)} duplicate rows")
        dup_species = duplicates[species_col].value_counts()
        print("\nTop 10 repeated species:")
        print(dup_species.head(10).to_string())
    else:
        print("\n✅ No duplicates found!")
    
    # Remove duplicates (keep first occurrence)
    df_clean = df.drop_duplicates(subset=[species_col], keep='first')
    
    print(f"\n📝 After deduplication:")
    print(f"   Rows: {len(df_clean)}")
    print(f"   Removed: {total_rows - len(df_clean)} rows")
    
    # Save
    df_clean.to_csv(output_file, index=False)
    print(f"✅ Saved to: {output_file}")
    
    return df_clean


if __name__ == "__main__":
    deduplicate_species_list()
