#!/usr/bin/env python3
"""
Verify enrichment impact: temporal coverage and indicator expansion (auditable).

Record_type logic (unified schema):
- observation: Measured value; has pillar, indicator, indicator_code, value_numeric, observation_date.
- event: Policy/launch/milestone; has category; pillar is EMPTY (effect on pillars via impact_link).
- impact_link: Links event to indicator. parent_id = event.record_id (forms the link);
  pillar = pillar of the indicator affected (related_indicator).

Parent_id links: Every impact_link.parent_id must equal some event.record_id. This script
verifies that all impact_link parent_ids exist in the event table after enrichment.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data import load_unified_data, enrich_unified_data
from src.data.enrichment import verify_enrichment_impact


def main():
    # Load raw (before enrichment)
    df_before = load_unified_data()
    # Enrich: constructs new observations, events, impact_links following unified schema
    df_after = enrich_unified_data(df_before.copy())

    result = verify_enrichment_impact(df_before, df_after)

    print("=" * 60)
    print("ENRICHMENT VERIFICATION — temporal coverage & indicator expansion")
    print("=" * 60)
    print("\n1. Record type counts (before -> after)")
    for rt in ["observation", "event", "impact_link", "target"]:
        b = result["record_type_counts_before"].get(rt, 0)
        a = result["record_type_counts_after"].get(rt, 0)
        print(f"   {rt}: {b} -> {a}")

    print("\n2. Temporal coverage (key indicators) — years with at least one observation")
    for code in ["ACC_OWNERSHIP", "USG_DIGITAL_PAY", "ACC_MM_ACCOUNT"]:
        before = result["temporal_coverage_before"].get(code, [])
        after = result["temporal_coverage_after"].get(code, [])
        print(f"   {code}: before {before} -> after {after}")

    print("\n3. Indicator expansion (new indicator_codes added by enrichment)")
    print("   ", result["indicators_added"] or "(none)")

    print("\n4. Years expanded for existing indicators (new years added by enrichment)")
    for code, years in result.get("years_expanded_for_existing_indicators", {}).items():
        print(f"   {code}: new years {years}")

    print("\n5. parent_id link check (every impact_link.parent_id must be an event.record_id)")
    print("   event record_ids:", result["event_ids"])
    print("   impact_link parent_ids:", result["impact_parent_ids"])
    print("   All parent_ids valid:", result["parent_id_links_valid"])

    print("\n" + "=" * 60)
    return 0 if result["parent_id_links_valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
