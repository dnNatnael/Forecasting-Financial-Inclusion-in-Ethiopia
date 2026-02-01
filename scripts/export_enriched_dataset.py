#!/usr/bin/env python3
"""
Export the enriched unified dataset (Task 1) to CSV and optionally Excel.

Run from project root: python scripts/export_enriched_dataset.py

Outputs:
- data/processed/ethiopia_fi_unified_data_enriched.csv  (all record_types, single file)
- data/processed/ethiopia_fi_unified_data_enriched.xlsx (Sheet 1: data without impact_link; Sheet 2: impact_links)
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd
from src.data import load_unified_data, enrich_unified_data


def main():
    out_dir = ROOT / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_unified_data()
    df = enrich_unified_data(df)

    # Single CSV (all record_types)
    csv_path = out_dir / "ethiopia_fi_unified_data_enriched.csv"
    df.to_csv(csv_path, index=False)
    print("Written: {}".format(csv_path))

    # Excel: Sheet 1 = data (observation, event, target); Sheet 2 = impact_links
    data_sheet = df[df["record_type"] != "impact_link"].copy()
    impact_sheet = df[df["record_type"] == "impact_link"].copy()
    xlsx_path = out_dir / "ethiopia_fi_unified_data_enriched.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as w:
        data_sheet.to_excel(w, sheet_name="ethiopia_fi_unified_data", index=False)
        impact_sheet.to_excel(w, sheet_name="Impact_sheet", index=False)
    print("Written: {}".format(xlsx_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
