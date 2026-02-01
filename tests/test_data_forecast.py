"""Minimal tests for data loading and forecasting."""

from pathlib import Path

import pytest

# Project root
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def unified_df():
    import sys
    sys.path.insert(0, str(ROOT))
    from src.data import load_unified_data, enrich_unified_data
    df = load_unified_data()
    return enrich_unified_data(df)


def test_load_has_record_types(unified_df):
    assert "record_type" in unified_df.columns
    assert set(unified_df["record_type"].unique()) >= {"observation", "event", "target", "impact_link"}


def test_access_series(unified_df):
    import sys
    sys.path.insert(0, str(ROOT))
    from src.analysis import get_access_series
    acc = get_access_series(unified_df, indicator_code="ACC_OWNERSHIP")
    assert len(acc) >= 1
    assert acc.max() <= 100 and acc.min() >= 0


def test_forecast_shape(unified_df):
    import sys
    sys.path.insert(0, str(ROOT))
    from src.models import forecast_access_usage
    access_f, usage_f = forecast_access_usage(unified_df, forecast_years=[2025, 2026, 2027])
    assert len(access_f) == 3 and list(access_f["year"]) == [2025, 2026, 2027]
    assert len(usage_f) == 3 and list(usage_f["year"]) == [2025, 2026, 2027]
