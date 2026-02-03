"""
Forecast Access (Account Ownership) and Usage (Digital Payment Adoption) for 2025–2027.

Combines:
- Historical time series (Findex + enriched)
- Simple trend (linear or growth rate)
- Event-impact adjustments from impact_link (lagged effects)
- Confidence intervals (trend uncertainty; sparse-data limitations)
- Scenarios: optimistic, base, pessimistic (event-effect multipliers)
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


def _get_event_delta(
    year: int,
    impact_matrix: pd.DataFrame,
    indicator_code: str,
) -> float:
    """Sum of event effects (in percentage points) for the given year and indicator."""
    if impact_matrix is None or impact_matrix.empty:
        return 0.0
    return apply_event_impacts(0.0, year, impact_matrix, indicator_code, unit_is_percentage=True)


def _trend_forecast_with_ci(
    series: pd.Series,
    years_ahead: list[int],
    method: str = "linear",
    confidence: float = 0.95,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Trend forecast with point estimate and confidence intervals.

    Uses OLS on (year, value). Intervals widen for extrapolation (prediction interval).
    With sparse data (e.g. 5 points), intervals are wide; limitations should be acknowledged.

    Returns
    -------
    point : pd.Series, index = year, value = point forecast
    lower : pd.Series, lower bound of confidence interval
    upper : pd.Series, upper bound
    """
    try:
        import statsmodels.api as sm
    except ImportError:
        logger.warning("statsmodels not available; returning point forecast only, no CI")
        point = _trend_forecast(series, years_ahead, method=method)
        nan_ser = pd.Series({y: np.nan for y in years_ahead})
        return point, nan_ser.copy(), nan_ser.copy()

    if series.empty:
        nan_ser = pd.Series({y: np.nan for y in years_ahead})
        return nan_ser.copy(), nan_ser.copy(), nan_ser.copy()

    series = series.sort_index()
    if hasattr(series.index, "year"):
        valid_mask = pd.notna(series.index)
        if not valid_mask.all():
            series = series.loc[valid_mask]
    if series.empty:
        nan_ser = pd.Series({y: np.nan for y in years_ahead})
        return nan_ser.copy(), nan_ser.copy(), nan_ser.copy()

    year_index = series.index.year if hasattr(series.index, "year") else np.arange(len(series))
    vals = series.values
    by_year = pd.Series(vals, index=year_index).groupby(level=0).mean()
    years_hist = by_year.index.astype(int).tolist()
    vals_hist = by_year.values
    n = len(years_hist)
    if n < 2:
        point = _trend_forecast(series, years_ahead, method=method)
        nan_ser = pd.Series({y: np.nan for y in years_ahead})
        return point, nan_ser.copy(), nan_ser.copy()

    x = np.array(years_hist, dtype=float).reshape(-1, 1)
    x = sm.add_constant(x)
    y = vals_hist
    model = sm.OLS(y, x).fit()
    # Prediction interval for new years
    point_out = {}
    lower_out = {}
    upper_out = {}
    for y in years_ahead:
        if y <= max(years_hist) and y in years_hist:
            idx = years_hist.index(y)
            point_out[y] = float(vals_hist[idx])
            lower_out[y] = point_out[y]
            upper_out[y] = point_out[y]
            continue
        x_new = sm.add_constant(np.array([[y]]))
        pred = model.get_prediction(x_new)
        pred_summary = pred.summary_frame(alpha=1 - confidence)
        point_out[y] = float(pred_summary["mean"].iloc[0])
        lower_out[y] = float(pred_summary["obs_ci_lower"].iloc[0])
        upper_out[y] = float(pred_summary["obs_ci_upper"].iloc[0])
    return (
        pd.Series(point_out),
        pd.Series(lower_out),
        pd.Series(upper_out),
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


def forecast_access_usage_with_uncertainty(
    df: pd.DataFrame,
    access_code: str = "ACC_OWNERSHIP",
    usage_code: str = "USG_DIGITAL_PAY",
    forecast_years: Optional[list[int]] = None,
    apply_events: bool = True,
    trend_method: str = "linear",
    confidence: float = 0.95,
    scenario_optimistic_mult: float = 1.2,
    scenario_pessimistic_mult: float = 0.6,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Forecast Access and Usage with confidence intervals and scenario ranges.

    - Baseline: trend continuation (linear regression on historical years).
    - With events: baseline + event effects (impact_link, lagged).
    - CI: prediction interval from trend regression (wider with sparse data).
    - Scenarios: same trend; event effects scaled (optimistic 1.2x, pessimistic 0.6x).

    Parameters
    ----------
    df : pd.DataFrame
        Unified + enriched dataframe.
    access_code, usage_code : str
        Indicator codes for Access and Usage.
    forecast_years : list[int], optional
        Default [2025, 2026, 2027].
    apply_events : bool
        If True, add event impacts to baseline.
    trend_method : str
        'linear' or 'last'.
    confidence : float
        Confidence level for intervals (e.g. 0.95).
    scenario_optimistic_mult : float
        Multiplier on event delta for optimistic scenario (default 1.2).
    scenario_pessimistic_mult : float
        Multiplier on event delta for pessimistic scenario (default 0.6).

    Returns
    -------
    access_forecast : pd.DataFrame
        Columns: year, value_baseline, value_adjusted, ci_lower, ci_upper,
        scenario_optimistic, scenario_base, scenario_pessimistic, indicator.
    usage_forecast : pd.DataFrame
        Same structure.
    """
    forecast_years = forecast_years or [2025, 2026, 2027]
    _validate_forecast_inputs(df, forecast_years, apply_events)

    access_hist = get_access_series(df, indicator_code=access_code)
    usage_hist = get_usage_series(df, indicator_code=usage_code)
    if usage_hist.empty and usage_code == "USG_DIGITAL_PAY":
        usage_hist = get_usage_series(df, indicator_code="USG_ACTIVE_RATE")

    impact_matrix = build_impact_matrix(df) if apply_events else None

    def forecast_one_uncertain(
        hist: pd.Series,
        ind_code: str,
        name: str,
    ) -> pd.DataFrame:
        point, lower, upper = _trend_forecast_with_ci(
            hist, forecast_years, method=trend_method, confidence=confidence
        )
        rows = []
        for y in forecast_years:
            b = float(point.get(y, np.nan))
            delta = _get_event_delta(y, impact_matrix, ind_code) if apply_events and impact_matrix is not None else 0.0
            adj = b + delta if not np.isnan(b) else np.nan
            ci_lo = float(lower.get(y, np.nan))
            ci_hi = float(upper.get(y, np.nan))
            # Scenario: baseline + scaled event delta (CI bounds stay trend-only for clarity)
            opt = b + scenario_optimistic_mult * delta if not np.isnan(b) else np.nan
            pess = b + scenario_pessimistic_mult * delta if not np.isnan(b) else np.nan
            rows.append({
                "year": y,
                "value_baseline": b,
                "value_adjusted": adj,
                "ci_lower": ci_lo,
                "ci_upper": ci_hi,
                "scenario_optimistic": opt,
                "scenario_base": adj,
                "scenario_pessimistic": pess,
                "indicator": name,
            })
        return pd.DataFrame(rows)

    access_forecast = forecast_one_uncertain(access_hist, access_code, "Account Ownership (Access)")
    usage_forecast = forecast_one_uncertain(usage_hist, usage_code, "Digital Payment Adoption (Usage)")
    logger.info(
        "Forecast with uncertainty: %d years, confidence=%.2f, scenarios applied",
        len(forecast_years),
        confidence,
    )
    return access_forecast, usage_forecast
