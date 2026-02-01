"""
Event-impact modeling: map events to indicator effects using impact_link records.

Uses lag_months and impact_estimate (or impact_magnitude) to build a matrix
of (event_date + lag -> indicator -> effect) for use in forecasting.
"""

from typing import Optional

import pandas as pd


def build_impact_matrix(
    df: pd.DataFrame,
    events: Optional[pd.DataFrame] = None,
    impact_links: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Build a matrix: (event_id, related_indicator) -> impact_estimate, lag_months, impact_direction.

    Parameters
    ----------
    df : pd.DataFrame
        Full unified data (used to get events and impact_link if not provided).
    events : pd.DataFrame, optional
        Events with record_id, observation_date.
    impact_links : pd.DataFrame, optional
        impact_link rows with parent_id, related_indicator, impact_estimate, lag_months, impact_direction.

    Returns
    -------
    pd.DataFrame
        Columns: event_id, event_date, related_indicator, impact_estimate, lag_months, impact_direction.
    """
    if events is None:
        events = df[df["record_type"] == "event"][["record_id", "observation_date"]].copy()
    if impact_links is None:
        impact_links = df[df["record_type"] == "impact_link"].copy()
    events = events.rename(columns={"record_id": "event_id", "observation_date": "event_date"})
    impact_links = impact_links.rename(columns={"parent_id": "event_id"})
    merge = impact_links.merge(
        events,
        on="event_id",
        how="left",
    )
    cols = ["event_id", "event_date", "related_indicator", "impact_estimate", "lag_months", "impact_direction"]
    for c in cols:
        if c not in merge.columns:
            merge[c] = pd.NA
    return merge[cols].dropna(subset=["related_indicator"])


def apply_event_impacts(
    base_value: float,
    year: int,
    impact_matrix: pd.DataFrame,
    indicator_code: str,
    unit_is_percentage: bool = True,
) -> float:
    """
    Apply cumulative event effects to a base value for a given year.

    Effects that (event_date + lag_months) fall in the same calendar year
    are summed (as percentage-point or ratio deltas). impact_estimate is
    in percentage points when unit_is_percentage; otherwise treated as ratio.

    Parameters
    ----------
    base_value : float
        Baseline value (e.g. from trend forecast).
    year : int
        Calendar year for which to apply effects.
    impact_matrix : pd.DataFrame
        Output of build_impact_matrix (must have event_date, lag_months, impact_estimate, impact_direction).
    indicator_code : str
        Filter effects for this indicator (related_indicator).
    unit_is_percentage : bool
        If True, impact_estimate is in percentage points; else additive.

    Returns
    -------
    float
        base_value + sum of effects for that year/indicator.
    """
    imp = impact_matrix[impact_matrix["related_indicator"] == indicator_code].copy()
    if imp.empty:
        return base_value
    imp["event_date"] = pd.to_datetime(imp["event_date"])
    imp["lag_months"] = pd.to_numeric(imp["lag_months"], errors="coerce").fillna(0).astype(int)

    def add_months(d: pd.Timestamp, months: int) -> pd.Timestamp:
        year = d.year + (d.month - 1 + months) // 12
        month = (d.month - 1 + months) % 12 + 1
        day = min(d.day, pd.Timestamp(year=year, month=month, day=1).days_in_month)
        return pd.Timestamp(year=year, month=month, day=day)

    imp["effect_date"] = imp.apply(lambda r: add_months(r["event_date"], int(r["lag_months"])), axis=1)
    imp["effect_year"] = imp["effect_date"].dt.year
    imp = imp[imp["effect_year"] == year]
    if imp.empty:
        return base_value
    delta = 0.0
    for _, row in imp.iterrows():
        v = row.get("impact_estimate")
        est = 0.0 if pd.isna(v) else float(v)
        direction = str(row.get("impact_direction", "increase")).lower()
        if direction == "decrease":
            est = -est
        delta += est
    return base_value + delta if unit_is_percentage else base_value * (1 + delta / 100.0)
