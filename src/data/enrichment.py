"""
Enrich the unified financial inclusion dataset (Task 1).

Record_type logic (unified schema):
- observation: Actual measured value; must have pillar, indicator, indicator_code,
  value_numeric, observation_date. category is empty. Used for surveys, operator data.
- event: Policy/launch/milestone; must have category (e.g. policy, product_launch,
  regulation). pillar is left EMPTY — events are not assigned to a pillar; their
  effect on pillars is modeled via impact_link.
- impact_link: Links an event to an indicator. Must have parent_id (event's record_id),
  pillar (the pillar of the indicator affected), related_indicator (indicator_code),
  impact_direction, impact_magnitude, lag_months, evidence_basis. parent_id links are
  formed by setting parent_id = event.record_id (e.g. IMP_ENR_001.parent_id = "EVT_ENR_001").

Pillar handling:
- Observations: pillar is set (ACCESS, USAGE, AFFORDABILITY, GENDER, etc.).
- Events: pillar is None/empty.
- Impact_links: pillar is the pillar of the *indicator* that the event affects
  (e.g. related_indicator=USG_DIGITAL_PAY -> pillar=USAGE).

Adds:
- Historical Findex baseline (2011 Account Ownership 14%) for continuity.
- Digital Payment Adoption Rate (Usage pillar); placeholders and usage observations.
- One new event (NBE Interoperability Directive); two new impact_links.
Verification: use verify_enrichment_impact() to audit temporal coverage and indicator expansion.
"""

from pathlib import Path
from typing import Optional

import pandas as pd


# Schema columns (subset used for new rows). Must match load.py unified output.
UNIFIED_COLS = [
    "record_id", "record_type", "category", "pillar", "indicator", "indicator_code",
    "indicator_direction", "value_numeric", "value_text", "value_type", "unit",
    "observation_date", "period_start", "period_end", "fiscal_year", "gender",
    "location", "region", "source_name", "source_type", "source_url", "confidence",
    "related_indicator", "relationship_type", "impact_direction", "impact_magnitude",
    "impact_estimate", "lag_months", "evidence_basis", "comparable_country",
    "collected_by", "collection_date", "original_text", "notes",
]
# parent_id exists only on impact_link rows; it holds the event's record_id (event.record_id).
# Main dataframe may have parent_id as NaN for non-impact_link rows after load_unified_data().
OPTIONAL_COLS = ["parent_id"]


COLLECTION_DATE = "2025-02-01"
COLLECTED_BY = "Selam Analytics (Task 1)"


def _row(
    record_id: str,
    pillar: str,
    indicator: str,
    indicator_code: str,
    value_numeric: float,
    unit: str,
    observation_date: str,
    value_type: str = "percentage",
    indicator_direction: str = "higher_better",
    source_name: str = "",
    source_type: str = "",
    source_url: str = "",
    confidence: str = "medium",
    original_text: Optional[str] = None,
    collected_by: str = COLLECTED_BY,
    collection_date: str = COLLECTION_DATE,
    notes: str = "",
) -> dict:
    """Build one observation row: record_type='observation', pillar set (required for observations)."""
    return {
        "record_id": record_id,
        "record_type": "observation",  # measured value; pillar must be set
        "category": None,
        "pillar": pillar,
        "indicator": indicator,
        "indicator_code": indicator_code,
        "indicator_direction": indicator_direction,
        "value_numeric": value_numeric,
        "value_text": None,
        "value_type": value_type,
        "unit": unit,
        "observation_date": pd.to_datetime(observation_date),
        "period_start": pd.NaT,
        "period_end": pd.NaT,
        "fiscal_year": pd.NA,
        "gender": "all",
        "location": "national",
        "region": None,
        "source_name": source_name,
        "source_type": source_type,
        "source_url": source_url,
        "confidence": confidence,
        "related_indicator": None,
        "relationship_type": None,
        "impact_direction": None,
        "impact_magnitude": None,
        "impact_estimate": None,
        "lag_months": None,
        "evidence_basis": None,
        "comparable_country": None,
        "collected_by": collected_by,
        "collection_date": collection_date,
        "original_text": original_text,
        "notes": notes,
    }


def _enrichment_observations() -> pd.DataFrame:
    """Build dataframe of new observations to add (Task 1 enrichment)."""
    rows = []

    # --- 1. Historical Findex baseline (2011) ---
    rows.append(
        _row(
            "REC_ENR_001",
            "ACCESS",
            "Account Ownership Rate",
            "ACC_OWNERSHIP",
            14.0,
            "%",
            "2011-12-31",
            source_name="Global Findex 2011",
            source_type="survey",
            source_url="https://www.worldbank.org/en/publication/globalfindex",
            confidence="high",
            original_text="Ethiopia account ownership 14% (2011). World Bank Global Findex Database.",
            notes="Baseline year (Findex); added for continuity.",
        )
    )

    # --- 2. Digital Payment Adoption Rate (Usage) — Findex definition ---
    # "Share of adults who made or received digital payment in past 12 months"
    # 2024 ~35%; approximate 2021 from context (pre-Telebirr scale-up).
    for year, val in [(2021, 18.0), (2024, 35.0)]:
        rows.append(
            _row(
                f"REC_ENR_002_{year}",
                "USAGE",
                "Digital Payment Adoption Rate",
                "USG_DIGITAL_PAY",
                val,
                "%",
                f"{year}-12-31",
                source_name="Global Findex" if year == 2024 else "Estimated from Findex/operator context",
                source_type="survey" if year == 2024 else "estimated",
                source_url="https://www.worldbank.org/en/publication/globalfindex" if year == 2024 else "",
                confidence="high" if year == 2024 else "estimated",
                original_text="Made or received digital payment in past 12 months (%)." if year == 2024 else None,
                notes="Findex: made or received digital payment (past 12 months)." if year == 2024 else "Approximate pre–digital surge.",
            )
        )

    # --- 3. Direct correlation (Guide B): structure for IMF FAS / NBE ---
    # Agent density (agents per 10k adults) — placeholder for FSD/NBE
    rows.append(
        _row(
            "REC_ENR_003",
            "USAGE",
            "Agent Density (per 10k adults)",
            "USG_AGENT_DENSITY",
            0.0,  # placeholder: to be filled from FSD/NBE
            "per 10k adults",
            "2024-12-31",
            value_type="rate",
            source_name="To be collected – FSD / NBE",
            source_type="regulator",
            confidence="estimated",
            notes="Direct correlation (Guide B). Fill from FSD or NBE when available.",
        )
    )
    # ATM density (per 100k adults) — IMF FAS style
    rows.append(
        _row(
            "REC_ENR_004",
            "ACCESS",
            "ATM Density (per 100k adults)",
            "ACC_ATM_DENSITY",
            0.0,  # placeholder
            "per 100k adults",
            "2024-12-31",
            value_type="rate",
            source_name="IMF FAS / NBE",
            source_type="regulator",
            confidence="estimated",
            notes="IMF Financial Access Survey; Ethiopia included.",
        )
    )
    # Bank branches per 100k adults
    rows.append(
        _row(
            "REC_ENR_005",
            "ACCESS",
            "Bank Branch Density (per 100k adults)",
            "ACC_BRANCH_DENSITY",
            0.0,  # placeholder
            "per 100k adults",
            "2024-12-31",
            value_type="rate",
            source_name="IMF FAS / NBE",
            source_type="regulator",
            confidence="estimated",
            notes="Supply-side access; IMF FAS.",
        )
    )

    # --- 4. Indirect (Guide C): smartphone penetration, mobile internet ---
    rows.append(
        _row(
            "REC_ENR_006",
            "ACCESS",
            "Smartphone Penetration",
            "ACC_SMARTPHONE_PEN",
            0.0,  # placeholder: GSMA/ITU
            "%",
            "2024-12-31",
            source_name="To be collected – GSMA / ITU",
            source_type="research",
            confidence="estimated",
            notes="Indirect enabler (Guide C).",
        )
    )
    rows.append(
        _row(
            "REC_ENR_007",
            "ACCESS",
            "Mobile Internet Usage (% adults)",
            "ACC_MOBILE_INTERNET",
            0.0,  # placeholder
            "%",
            "2024-12-31",
            source_name="To be collected – ITU / GSMA",
            source_type="research",
            confidence="estimated",
            notes="Indirect; captures effective connectivity.",
        )
    )

    # --- 5. Used account to receive wages (Usage) — Findex 2024 ---
    rows.append(
        _row(
            "REC_ENR_008",
            "USAGE",
            "Used Account to Receive Wages",
            "USG_WAGES",
            15.0,
            "%",
            "2024-12-31",
            source_name="Global Findex 2024",
            source_type="survey",
            source_url="https://www.worldbank.org/en/publication/globalfindex",
            confidence="high",
            original_text="Share of adults who used an account to receive wages in the past 12 months; Ethiopia ~15% (2024).",
            notes="Direct usage indicator; useful for forecasting digital payment adoption.",
        )
    )

    return pd.DataFrame(rows)


def _enrichment_events() -> pd.DataFrame:
    """New events: record_type='event', category filled, pillar left EMPTY (events are not assigned to a pillar)."""
    base = {
        "record_type": "event",
        "category": None,  # set per row below
        "pillar": None,   # schema: events have no pillar; effect on pillars is via impact_link
        "indicator_direction": None,
        "value_numeric": None,
        "value_text": None,
        "value_type": None,
        "unit": None,
        "period_start": pd.NaT,
        "period_end": pd.NaT,
        "fiscal_year": None,
        "gender": "all",
        "location": "national",
        "region": None,
        "related_indicator": None,
        "relationship_type": None,
        "impact_direction": None,
        "impact_magnitude": None,
        "impact_estimate": None,
        "lag_months": None,
        "evidence_basis": None,
        "comparable_country": None,
        "collected_by": COLLECTED_BY,
        "collection_date": COLLECTION_DATE,
        "parent_id": None,  # events do not have parent_id; only impact_link rows do
    }
    rows = [
        {
            **base,
            "record_id": "EVT_ENR_001",  # referenced by IMP_ENR_001.parent_id
            "indicator": "NBE Interoperability Directive",
            "indicator_code": "EVT_INTEROP_DIR",
            "observation_date": pd.to_datetime("2024-06-01"),
            "source_name": "NBE",
            "source_type": "regulator",
            "source_url": "https://nbe.gov.et",
            "confidence": "high",
            "original_text": "National Bank of Ethiopia directive on interoperability of mobile money and payment systems.",
            "notes": "Enables cross-platform P2P and merchant payments; supports Usage forecasting.",
            "value_text": "Implemented",
            "category": "regulation",
        },
    ]
    return pd.DataFrame(rows)


def _enrichment_impact_links() -> pd.DataFrame:
    """New impact_links: parent_id = event.record_id (links to event); pillar = pillar of the indicator affected."""
    base = {
        "record_type": "impact_link",  # relationship row; must have parent_id pointing to event
        "category": None,
        "indicator_direction": None,
        "value_numeric": None,
        "value_text": None,
        "value_type": None,
        "unit": None,
        "period_start": pd.NaT,
        "period_end": pd.NaT,
        "fiscal_year": None,
        "gender": "all",
        "location": "national",
        "region": None,
        "source_name": None,
        "source_type": None,
        "source_url": None,
        "confidence": None,
        "comparable_country": None,
        "collected_by": COLLECTED_BY,
        "collection_date": COLLECTION_DATE,
        "original_text": None,
        "notes": None,
    }
    rows = [
        {
            **base,
            "record_id": "IMP_ENR_001",
            "parent_id": "EVT_ENR_001",  # link to new event (NBE Interop); event.record_id
            "pillar": "USAGE",            # pillar of related_indicator (USG_DIGITAL_PAY is Usage)
            "indicator": "NBE Interop effect on Digital Payment Adoption",
            "indicator_code": None,
            "related_indicator": "USG_DIGITAL_PAY",
            "relationship_type": "direct",
            "impact_direction": "increase",
            "impact_magnitude": "medium",
            "impact_estimate": 5.0,
            "lag_months": 12,
            "evidence_basis": "literature",
            "observation_date": pd.to_datetime("2024-06-01"),
            "notes": "Interoperability typically raises digital payment usage (Tanzania, India).",
        },
        {
            **base,
            "record_id": "IMP_ENR_002",
            "parent_id": "EVT_0004",     # link to existing event (Fayda Digital ID Program Rollout)
            "pillar": "USAGE",            # related_indicator USG_DIGITAL_PAY is Usage pillar
            "indicator": "Fayda effect on Digital Payment Adoption",
            "indicator_code": None,
            "related_indicator": "USG_DIGITAL_PAY",
            "relationship_type": "enabling",
            "impact_direction": "increase",
            "impact_magnitude": "low",
            "impact_estimate": 3.0,
            "lag_months": 24,
            "evidence_basis": "literature",
            "observation_date": pd.to_datetime("2024-01-01"),
            "notes": "Digital ID enables account opening and payments; indirect effect on usage.",
        },
    ]
    return pd.DataFrame(rows)


def verify_enrichment_impact(
    df_before: pd.DataFrame,
    df_after: pd.DataFrame,
) -> dict:
    """
    Verify enrichment impact: temporal coverage and indicator expansion (auditable).

    - Compares record_type counts before vs after.
    - For observations: years present per indicator_code (temporal coverage);
      indicator_codes that appear only after enrichment (indicator expansion).
    - Verifies parent_id links: every impact_link.parent_id must equal some event.record_id.

    Returns
    -------
    dict with keys: record_type_counts_before, record_type_counts_after,
    temporal_coverage_before, temporal_coverage_after, indicators_added,
    parent_id_links_valid, event_ids, impact_parent_ids.
    """
    obs_before = df_before[df_before["record_type"] == "observation"]
    obs_after = df_after[df_after["record_type"] == "observation"]
    events_after = df_after[df_after["record_type"] == "event"]
    impact_after = df_after[df_after["record_type"] == "impact_link"]

    def _coverage(obs: pd.DataFrame) -> dict:
        if obs.empty or "indicator_code" not in obs.columns:
            return {}
        obs = obs.dropna(subset=["observation_date", "indicator_code"])
        obs["year"] = pd.to_datetime(obs["observation_date"]).dt.year
        return obs.groupby("indicator_code")["year"].apply(lambda x: sorted(x.unique().tolist())).to_dict()

    cov_before = _coverage(obs_before)
    cov_after = _coverage(obs_after)
    codes_before = set(cov_before.keys())
    codes_after = set(cov_after.keys())
    indicators_added = list(codes_after - codes_before)
    # For existing codes, list years added (temporal expansion)
    years_expanded = {}
    for code in codes_before & codes_after:
        y_b, y_a = set(cov_before.get(code, [])), set(cov_after.get(code, []))
        new_years = y_a - y_b
        if new_years:
            years_expanded[code] = sorted(new_years)

    event_ids = set(events_after["record_id"].dropna().astype(str))
    impact_parent_ids = set(impact_after["parent_id"].dropna().astype(str))
    parent_id_links_valid = impact_parent_ids <= event_ids if impact_parent_ids else True

    return {
        "record_type_counts_before": df_before["record_type"].value_counts().to_dict(),
        "record_type_counts_after": df_after["record_type"].value_counts().to_dict(),
        "temporal_coverage_before": cov_before,
        "temporal_coverage_after": cov_after,
        "indicators_added": indicators_added,
        "years_expanded_for_existing_indicators": years_expanded,
        "parent_id_links_valid": parent_id_links_valid,
        "event_ids": list(event_ids),
        "impact_parent_ids": list(impact_parent_ids),
    }


def enrich_unified_data(
    df: pd.DataFrame,
    enrichment_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Append Task 1 enrichment: observations, events, and impact_links.

    Construction follows unified schema: observations have pillar set; events have
    category set and pillar empty; impact_links have parent_id (event record_id),
    pillar (of the indicator affected), related_indicator, impact_*, lag_months, evidence_basis.
    Run verify_enrichment_impact(df_before, df_after) to audit temporal coverage and expansion.

    Parameters
    ----------
    df : pd.DataFrame
        Output of load_unified_data().
    enrichment_path : Path, optional
        Unused; reserved for future CSV/Excel of external enrichment.

    Returns
    -------
    pd.DataFrame
        df with additional observation (REC_ENR_*), event (EVT_ENR_*), and
        impact_link (IMP_ENR_*) rows. Same columns; parent_id present for impact_link.
    """
    extra_obs = _enrichment_observations()
    extra_events = _enrichment_events()
    extra_impact = _enrichment_impact_links()

    def align_and_concat(extra: pd.DataFrame) -> pd.DataFrame:
        for c in extra.columns:
            if c not in df.columns:
                df[c] = pd.NA
        for c in df.columns:
            if c not in extra.columns:
                extra[c] = pd.NA
        return extra[[c for c in df.columns if c in extra.columns]]

    extra_obs = align_and_concat(extra_obs.copy())
    extra_events = align_and_concat(extra_events.copy())
    extra_impact = align_and_concat(extra_impact.copy())
    return pd.concat([df, extra_obs, extra_events, extra_impact], ignore_index=True)
