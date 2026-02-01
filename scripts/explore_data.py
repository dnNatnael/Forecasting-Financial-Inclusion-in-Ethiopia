#!/usr/bin/env python3
"""
Task 1: Data Exploration — Load all three datasets and explore structure.

Run from project root: python scripts/explore_data.py

Outputs:
- Counts by record_type, pillar, source_type, confidence
- Temporal range of observations
- Unique indicators (indicator_code) and coverage
- Events catalog and dates
- Impact_links summary
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd
from src.data import load_unified_data, load_reference_codes, load_guide


def main():
    print("=" * 60)
    print("TASK 1: DATA EXPLORATION")
    print("=" * 60)

    # --- Load all three datasets ---
    print("\n1. LOADING ALL THREE DATASETS")
    print("-" * 40)
    try:
        df = load_unified_data()
        print("  [OK] ethiopia_fi_unified_data: {} rows".format(len(df)))
    except Exception as e:
        print("  [FAIL] ethiopia_fi_unified_data:", e)
        return 1
    try:
        ref = load_reference_codes()
        print("  [OK] reference_codes: {} sheet(s)".format(len(ref)))
    except Exception as e:
        print("  [FAIL] reference_codes:", e)
        return 1
    try:
        guide = load_guide()
        print("  [OK] Additional Data Points Guide: {} sheet(s)".format(len(guide)))
    except Exception as e:
        print("  [FAIL] Additional Data Points Guide:", e)
        return 1

    # --- Schema: shared columns ---
    print("\n2. SCHEMA (shared columns)")
    print("-" * 40)
    print("  Columns ({}): {}".format(len(df.columns), ", ".join(df.columns[:12])) + " ..." if len(df.columns) > 12 else "")
    print("  record_type values:", df["record_type"].unique().tolist())

    # --- Counts ---
    print("\n3. COUNTS BY record_type, pillar, source_type, confidence")
    print("-" * 40)
    print("  record_type:")
    for k, v in df["record_type"].value_counts().items():
        print("    {}: {}".format(k, v))
    obs = df[df["record_type"] == "observation"]
    if not obs.empty:
        print("  pillar (observations only):")
        for k, v in obs["pillar"].value_counts().items():
            print("    {}: {}".format(k, v))
        print("  source_type (observations only):")
        for k, v in obs["source_type"].value_counts().items():
            print("    {}: {}".format(k, v))
        print("  confidence (observations only):")
        for k, v in obs["confidence"].value_counts().items():
            print("    {}: {}".format(k, v))

    # --- Temporal range ---
    print("\n4. TEMPORAL RANGE OF OBSERVATIONS")
    print("-" * 40)
    obs_dates = pd.to_datetime(obs["observation_date"], errors="coerce").dropna()
    if len(obs_dates) > 0:
        print("  Min date: {}".format(obs_dates.min()))
        print("  Max date: {}".format(obs_dates.max()))
        print("  Years present: {}".format(sorted(obs_dates.dt.year.unique().tolist())))
    else:
        print("  No observation_date found.")

    # --- Unique indicators and coverage ---
    print("\n5. UNIQUE INDICATORS (indicator_code) AND COVERAGE")
    print("-" * 40)
    if "indicator_code" in obs.columns:
        grp = obs.dropna(subset=["indicator_code"]).groupby("indicator_code")
        for code, g in grp:
            ind = g["indicator"].iloc[0]
            pillar = g["pillar"].iloc[0]
            n_obs = len(g)
            dates = pd.to_datetime(g["observation_date"], errors="coerce").dropna()
            dr = "{} - {}".format(dates.min(), dates.max()) if len(dates) else "N/A"
            print("  {} ({}): {} obs, {}".format(code, pillar, n_obs, dr))

    # --- Events ---
    print("\n6. EVENTS CATALOG AND DATES")
    print("-" * 40)
    events = df[df["record_type"] == "event"].copy()
    events["observation_date"] = pd.to_datetime(events["observation_date"], errors="coerce")
    events = events.sort_values("observation_date")
    for _, r in events.iterrows():
        print("  {} | {} | {} | {}".format(
            r.get("observation_date", ""),
            r.get("category", ""),
            r.get("indicator", ""),
            r.get("record_id", ""),
        ))

    # --- Impact links ---
    print("\n7. IMPACT_LINKS (event -> indicator relationships)")
    print("-" * 40)
    impact = df[df["record_type"] == "impact_link"]
    if not impact.empty:
        for _, r in impact.iterrows():
            print("  {} -> {} | impact_est={} lag_months={} direction={}".format(
                r.get("parent_id", ""),
                r.get("related_indicator", ""),
                r.get("impact_estimate", ""),
                r.get("lag_months", ""),
                r.get("impact_direction", ""),
            ))
    else:
        print("  No impact_link records.")

    print("\n" + "=" * 60)
    print("Exploration complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
