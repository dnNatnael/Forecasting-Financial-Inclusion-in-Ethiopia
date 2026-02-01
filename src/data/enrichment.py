"""
Enrich the unified financial inclusion dataset (Task 1).

Adds:
- Historical Findex baseline (2011 Account Ownership 14%) for continuity.
- Digital Payment Adoption Rate (Usage pillar) — Findex-defined; 2024 ~35%.
- Placeholder/alternative observations from the Additional Data Points Guide:
  - Direct: agent density, ATM density, bank branches (structure for IMF FAS / NBE).
  - Indirect: smartphone penetration, mobile internet (structure for GSMA/ITU).
All new rows use the same unified schema and record_type='observation'.
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
# parent_id only in impact_link; we add it when merging
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
    """Build one observation row with unified schema and documentation fields."""
    return {
        "record_id": record_id,
        "record_type": "observation",
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
    """New events (category filled; pillar left empty per schema)."""
    base = {
        "record_type": "event",
        "category": None,
        "pillar": None,
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
        "parent_id": None,
    }
    rows = [
        {
            **base,
            "record_id": "EVT_ENR_001",
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
    """New impact_links (parent_id -> event, pillar, related_indicator, impact_*, lag_months, evidence_basis)."""
    base = {
        "record_type": "impact_link",
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
            "parent_id": "EVT_ENR_001",
            "pillar": "USAGE",
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
            "parent_id": "EVT_0004",
            "pillar": "USAGE",
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


def enrich_unified_data(
    df: pd.DataFrame,
    enrichment_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Append Task 1 enrichment: observations, events, and impact_links.

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
