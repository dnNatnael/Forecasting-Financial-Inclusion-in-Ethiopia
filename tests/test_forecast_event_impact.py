"""Unit tests for forecast and event-impact edge cases and validation."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


def _minimal_unified_df():
    """Minimal unified dataframe with required columns for forecasting."""
    return pd.DataFrame({
        "record_type": ["observation", "observation", "event", "impact_link"],
        "indicator_code": ["ACC_OWNERSHIP", "USG_DIGITAL_PAY", None, None],
        "observation_date": ["2020-01-01", "2020-01-01", "2022-06-15", None],
        "value_numeric": [40.0, 20.0, np.nan, np.nan],
        "location": ["national", "national", None, None],
        "gender": ["all", "all", None, None],
        "record_id": [None, None, "evt1", None],
        "parent_id": [None, None, None, "evt1"],
        "related_indicator": [None, None, None, "ACC_OWNERSHIP"],
    })


# ----- Forecast validation and edge cases -----


def test_forecast_raises_on_none_df():
    import sys
    sys.path.insert(0, str(ROOT))
    from src.models import forecast_access_usage
    with pytest.raises(ValueError, match="df must be a non-null pandas DataFrame"):
        forecast_access_usage(None, forecast_years=[2025])


def test_forecast_raises_on_empty_df():
    import sys
    sys.path.insert(0, str(ROOT))
    from src.models import forecast_access_usage
    with pytest.raises(ValueError, match="df is empty"):
        forecast_access_usage(pd.DataFrame(), forecast_years=[2025])


def test_forecast_raises_on_missing_columns():
    import sys
    sys.path.insert(0, str(ROOT))
    from src.models import forecast_access_usage
    df = pd.DataFrame({"record_type": ["observation"], "indicator_code": ["ACC"]})
    with pytest.raises(ValueError, match="missing required columns"):
        forecast_access_usage(df, forecast_years=[2025])


def test_forecast_raises_on_empty_forecast_years():
    import sys
    sys.path.insert(0, str(ROOT))
    from src.models import forecast_access_usage
    df = _minimal_unified_df()
    with pytest.raises(ValueError, match="forecast_years must be a non-empty list"):
        forecast_access_usage(df, forecast_years=[], apply_events=False)


def test_forecast_raises_on_invalid_forecast_years():
    import sys
    sys.path.insert(0, str(ROOT))
    from src.models import forecast_access_usage
    df = _minimal_unified_df()
    with pytest.raises(ValueError, match="invalid:"):
        forecast_access_usage(df, forecast_years=[2025, 1800], apply_events=False)
    with pytest.raises(ValueError, match="invalid:"):
        forecast_access_usage(df, forecast_years=[2025, 9999], apply_events=False)


def test_forecast_empty_series_returns_nan_baseline():
    import sys
    sys.path.insert(0, str(ROOT))
    from src.models import forecast_access_usage
    # No observations for the indicators -> empty series
    df = pd.DataFrame({
        "record_type": ["event"],
        "indicator_code": [None],
        "observation_date": [None],
        "value_numeric": [np.nan],
        "location": [None],
        "gender": [None],
        "record_id": ["evt1"],
        "parent_id": [None],
        "related_indicator": [None],
    })
    access_f, usage_f = forecast_access_usage(df, forecast_years=[2025, 2026], apply_events=False)
    assert len(access_f) == 2 and len(usage_f) == 2
    assert access_f["value_baseline"].isna().all()
    assert usage_f["value_baseline"].isna().all()


def test_forecast_single_year_baseline():
    import sys
    sys.path.insert(0, str(ROOT))
    from src.models import forecast_access_usage
    df = _minimal_unified_df()
    access_f, usage_f = forecast_access_usage(
        df, forecast_years=[2025], apply_events=False, trend_method="last"
    )
    assert list(access_f["year"]) == [2025]
    assert access_f["value_baseline"].notna().all()
    assert access_f["value_adjusted"].notna().all()


def test_forecast_apply_events_false_skips_impact_columns_check():
    import sys
    sys.path.insert(0, str(ROOT))
    from src.models import forecast_access_usage
    # Has observation columns but no parent_id/related_indicator (no impact_link)
    df = pd.DataFrame({
        "record_type": ["observation"],
        "indicator_code": ["ACC_OWNERSHIP"],
        "observation_date": ["2020-01-01"],
        "value_numeric": [50.0],
        "location": ["national"],
        "gender": ["all"],
    })
    access_f, usage_f = forecast_access_usage(df, forecast_years=[2025], apply_events=False)
    assert len(access_f) == 1 and len(usage_f) == 1


# ----- Event-impact: build_impact_matrix -----


def test_build_impact_matrix_raises_on_none_df():
    import sys
    sys.path.insert(0, str(ROOT))
    from src.models.event_impact import build_impact_matrix
    with pytest.raises(ValueError, match="df must be a non-null pandas DataFrame"):
        build_impact_matrix(None)


def test_build_impact_matrix_empty_df_returns_empty():
    import sys
    sys.path.insert(0, str(ROOT))
    from src.models.event_impact import build_impact_matrix, _IMPACT_MATRIX_COLUMNS
    result = build_impact_matrix(pd.DataFrame())
    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == _IMPACT_MATRIX_COLUMNS
    assert len(result) == 0


def test_build_impact_matrix_raises_on_missing_record_type():
    import sys
    sys.path.insert(0, str(ROOT))
    from src.models.event_impact import build_impact_matrix
    df = pd.DataFrame({"record_id": [1], "observation_date": ["2020-01-01"]})
    with pytest.raises(ValueError, match="record_type"):
        build_impact_matrix(df)


def test_build_impact_matrix_invalid_dates_dropped():
    import sys
    sys.path.insert(0, str(ROOT))
    from src.models.event_impact import build_impact_matrix
    df = pd.DataFrame({
        "record_type": ["event", "event", "impact_link", "impact_link"],
        "record_id": ["e1", "e2", None, None],
        "observation_date": ["2022-01-01", "not-a-date", None, None],
        "parent_id": [None, None, "e1", "e2"],
        "related_indicator": [None, None, "ACC_OWNERSHIP", "ACC_OWNERSHIP"],
    })
    result = build_impact_matrix(df)
    # Rows with valid event_date (e1) only; e2 has invalid date
    assert "event_date" in result.columns
    assert result["event_date"].notna().all()


# ----- Event-impact: apply_event_impacts -----


def test_apply_event_impacts_raises_on_none_matrix():
    import sys
    sys.path.insert(0, str(ROOT))
    from src.models.event_impact import apply_event_impacts
    with pytest.raises(ValueError, match="impact_matrix must be a non-null pandas DataFrame"):
        apply_event_impacts(50.0, 2025, None, "ACC_OWNERSHIP")


def test_apply_event_impacts_raises_on_missing_columns():
    import sys
    sys.path.insert(0, str(ROOT))
    from src.models.event_impact import apply_event_impacts
    matrix = pd.DataFrame({"related_indicator": ["ACC_OWNERSHIP"]})
    with pytest.raises(ValueError, match="missing required columns"):
        apply_event_impacts(50.0, 2025, matrix, "ACC_OWNERSHIP")


def test_apply_event_impacts_raises_on_non_int_year():
    import sys
    sys.path.insert(0, str(ROOT))
    from src.models.event_impact import apply_event_impacts
    matrix = pd.DataFrame({
        "related_indicator": [],
        "event_date": pd.to_datetime([]),
        "lag_months": [],
        "impact_estimate": [],
        "impact_direction": [],
    })
    with pytest.raises(ValueError, match="year must be an integer"):
        apply_event_impacts(50.0, 2025.5, matrix, "ACC_OWNERSHIP")


def test_apply_event_impacts_empty_matrix_returns_base():
    import sys
    sys.path.insert(0, str(ROOT))
    from src.models.event_impact import apply_event_impacts
    matrix = pd.DataFrame(columns=[
        "related_indicator", "event_date", "lag_months", "impact_estimate", "impact_direction"
    ])
    assert apply_event_impacts(50.0, 2025, matrix, "ACC_OWNERSHIP") == 50.0


def test_apply_event_impacts_no_matching_indicator_returns_base():
    import sys
    sys.path.insert(0, str(ROOT))
    from src.models.event_impact import apply_event_impacts
    matrix = pd.DataFrame({
        "related_indicator": ["OTHER_IND"],
        "event_date": [pd.Timestamp("2022-01-01")],
        "lag_months": [0],
        "impact_estimate": [5.0],
        "impact_direction": ["increase"],
    })
    assert apply_event_impacts(50.0, 2022, matrix, "ACC_OWNERSHIP") == 50.0


def test_apply_event_impacts_increase_direction_adds():
    import sys
    sys.path.insert(0, str(ROOT))
    from src.models.event_impact import apply_event_impacts
    matrix = pd.DataFrame({
        "related_indicator": ["ACC_OWNERSHIP"],
        "event_date": [pd.Timestamp("2022-01-01")],
        "lag_months": [0],
        "impact_estimate": [3.0],
        "impact_direction": ["increase"],
    })
    result = apply_event_impacts(50.0, 2022, matrix, "ACC_OWNERSHIP", unit_is_percentage=True)
    assert result == 53.0


def test_apply_event_impacts_decrease_direction_subtracts():
    import sys
    sys.path.insert(0, str(ROOT))
    from src.models.event_impact import apply_event_impacts
    matrix = pd.DataFrame({
        "related_indicator": ["ACC_OWNERSHIP"],
        "event_date": [pd.Timestamp("2022-01-01")],
        "lag_months": [0],
        "impact_estimate": [2.0],
        "impact_direction": ["decrease"],
    })
    result = apply_event_impacts(50.0, 2022, matrix, "ACC_OWNERSHIP", unit_is_percentage=True)
    assert result == 48.0


def test_apply_event_impacts_effect_in_target_year_only():
    import sys
    sys.path.insert(0, str(ROOT))
    from src.models.event_impact import apply_event_impacts
    matrix = pd.DataFrame({
        "related_indicator": ["ACC_OWNERSHIP"],
        "event_date": [pd.Timestamp("2022-06-01")],
        "lag_months": [0],
        "impact_estimate": [5.0],
        "impact_direction": ["increase"],
    })
    assert apply_event_impacts(50.0, 2022, matrix, "ACC_OWNERSHIP") == 55.0
    assert apply_event_impacts(50.0, 2023, matrix, "ACC_OWNERSHIP") == 50.0


def test_apply_event_impacts_nan_base_returns_as_is():
    import sys
    sys.path.insert(0, str(ROOT))
    from src.models.event_impact import apply_event_impacts
    matrix = pd.DataFrame(columns=[
        "related_indicator", "event_date", "lag_months", "impact_estimate", "impact_direction"
    ])
    out = apply_event_impacts(float("nan"), 2025, matrix, "ACC_OWNERSHIP")
    assert np.isnan(out)
