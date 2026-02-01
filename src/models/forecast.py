"""
Forecast Access (Account Ownership) and Usage (Digital Payment Adoption) for 2025–2027.

Combines:
- Historical time series (Findex + enriched)
- Simple trend (linear or growth rate)
- Event-impact adjustments from impact_link (lagged effects)
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

from ..analysis.eda import get_access_series, get_usage_series
from .event_impact import build_impact_matrix, apply_event_impacts

logger = logging.getLogger(__name__)

# Required columns for unified dataframe used in forecasting
_REQUIRED_OBS_COLUMNS = ["record_type", "indicator_code", "observation_date", "value_numeric"]
_REQUIRED_IMPACT_COLUMNS = ["record_type", "parent_id", "related_indicator"]
_MIN_YEAR, _MAX_YEAR = 1900, 2100


def _validate_forecast_inputs(
    df: pd.DataFrame,
    forecast_years: list[int],
    apply_events: bool,
) -> None:
    """Validate inputs for forecast_access_usage; raise ValueError with informative message."""
    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError("df must be a non-null pandas DataFrame")
    if df.empty:
        raise ValueError("df is empty; cannot produce forecasts without data")
    missing_obs = [c for c in _REQUIRED_OBS_COLUMNS if c not in df.columns]
    if missing_obs:
        raise ValueError(
            f"df is missing required columns for observations: {missing_obs}. "
            f"Expected at least: {_REQUIRED_OBS_COLUMNS}"
        )
    if apply_events:
        missing_impact = [c for c in _REQUIRED_IMPACT_COLUMNS if c not in df.columns]
        if missing_impact:
            raise ValueError(
                f"df is missing required columns for impact_link when apply_events=True: {missing_impact}. "
                f"Expected: {_REQUIRED_IMPACT_COLUMNS}"
            )
    if not forecast_years:
        raise ValueError("forecast_years must be a non-empty list of years")
    invalid_years = [y for y in forecast_years if not isinstance(y, int) or y < _MIN_YEAR or y > _MAX_YEAR]
    if invalid_years:
        raise ValueError(
            f"forecast_years must be integers between {_MIN_YEAR} and {_MAX_YEAR}; invalid: {invalid_years}"
        )


def _trend_forecast(
    series: pd.Series,
    years_ahead: list[int],
    method: str = "linear",
) -> pd.Series:
    """
    Extrapolate series by year using last observed year and trend.

    series: index = datetime (normalized to date), value = numeric.
    years_ahead: list of years to forecast (e.g. [2025, 2026, 2027]).
    method: 'linear' (regress value on year) or 'last' (flat at last value).
    """
    if series.empty:
        logger.warning("Trend forecast received empty series; returning NaN for all forecast years")
        return pd.Series({y: np.nan for y in years_ahead})
    series = series.sort_index()
    # Drop any rows with invalid (NaT) index dates
    if hasattr(series.index, "year"):
        valid_mask = pd.notna(series.index)
        if not valid_mask.all():
            n_invalid = (~valid_mask).sum()
            logger.warning("Dropping %d observation(s) with missing/invalid dates from series", n_invalid)
            series = series.loc[valid_mask]
        if series.empty:
            logger.warning("No valid dated observations left; returning NaN for all forecast years")
            return pd.Series({y: np.nan for y in years_ahead})
    # index may be DatetimeIndex or PeriodIndex; get year
    if hasattr(series.index, "year"):
        year_index = series.index.year
    else:
        year_index = np.arange(len(series))
    vals = series.values
    # one value per year (take mean if multiple obs per year)
    by_year = pd.Series(vals, index=year_index).groupby(level=0).mean()
    years_hist = by_year.index.astype(int).tolist()
    vals_hist = by_year.values
    last_year = int(max(years_hist))
    last_val = float(vals_hist[-1])

    out = {}
    for y in years_ahead:
        if y <= last_year and y in years_hist:
            out[y] = float(by_year.loc[y])
            continue
        if y <= last_year:
            out[y] = last_val
            continue
        if method == "last":
            out[y] = last_val
        else:
            # linear: regress value on year
            x = np.array(years_hist, dtype=float)
            coeffs = np.polyfit(x, vals_hist, 1)
            out[y] = float(np.polyval(coeffs, y))
    return pd.Series(out)


def forecast_access_usage(
    df: pd.DataFrame,
    access_code: str = "ACC_OWNERSHIP",
    usage_code: str = "USG_DIGITAL_PAY",
    forecast_years: Optional[list[int]] = None,
    apply_events: bool = True,
    trend_method: str = "linear",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Produce forecasts for Access and Usage for 2025–2027 (or custom years).

    Parameters
    ----------
    df : pd.DataFrame
        Unified + enriched dataframe (must include observations and impact_link).
    access_code : str
        Indicator code for Access (default ACC_OWNERSHIP).
    usage_code : str
        Indicator code for Usage (default USG_DIGITAL_PAY).
    forecast_years : list[int], optional
        Default [2025, 2026, 2027].
    apply_events : bool
        If True, adjust baseline trend with event impacts from impact_link.
    trend_method : str
        'linear' or 'last' for baseline trend.

    Returns
    -------
    access_forecast : pd.DataFrame
        Columns: year, value_baseline, value_adjusted (or value), source.
    usage_forecast : pd.DataFrame
        Same structure.
    """
    forecast_years = forecast_years or [2025, 2026, 2027]
    _validate_forecast_inputs(df, forecast_years, apply_events)

    logger.info("Building access series (indicator=%s) and usage series (indicator=%s)", access_code, usage_code)
    access_hist = get_access_series(df, indicator_code=access_code)
    usage_hist = get_usage_series(df, indicator_code=usage_code)

    if access_hist.empty:
        logger.warning("Access series is empty for indicator %s; baseline will be NaN", access_code)
    if usage_hist.empty and usage_code == "USG_DIGITAL_PAY":
        logger.info("Usage series empty for USG_DIGITAL_PAY; trying fallback USG_ACTIVE_RATE")
        usage_hist = get_usage_series(df, indicator_code="USG_ACTIVE_RATE")
    if usage_hist.empty:
        logger.warning("Usage series is empty; baseline will be NaN")

    impact_matrix = None
    if apply_events:
        impact_matrix = build_impact_matrix(df)
        if impact_matrix.empty:
            logger.info("Impact matrix is empty; forecasts will use baseline only")
        else:
            logger.info("Impact matrix has %d effect rows", len(impact_matrix))

    def forecast_one(hist: pd.Series, ind_code: str, name: str) -> pd.DataFrame:
        base = _trend_forecast(hist, forecast_years, method=trend_method)
        rows = []
        for y in forecast_years:
            b = float(base.get(y, np.nan))
            if apply_events and impact_matrix is not None and not np.isnan(b):
                adj = apply_event_impacts(b, y, impact_matrix, ind_code, unit_is_percentage=True)
            else:
                adj = b
            rows.append({"year": y, "value_baseline": b, "value_adjusted": adj, "indicator": name})
        return pd.DataFrame(rows)

    access_forecast = forecast_one(access_hist, access_code, "Account Ownership (Access)")
    usage_forecast = forecast_one(usage_hist, usage_code, "Digital Payment Adoption (Usage)")
    logger.info(
        "Forecast complete: %d years for access and usage (apply_events=%s)",
        len(forecast_years),
        apply_events,
    )
    return access_forecast, usage_forecast
