"""
Event-impact modeling: map events to indicator effects using impact_link records.

Uses lag_months and impact_estimate (or impact_magnitude) to build a matrix
of (event_date + lag -> indicator -> effect) for use in forecasting.
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Required columns when building from unified df
_EVENTS_COLUMNS = ["record_id", "observation_date"]
_IMPACT_LINK_COLUMNS = ["parent_id", "related_indicator"]
_IMPACT_MATRIX_COLUMNS = ["event_id", "event_date", "related_indicator", "impact_estimate", "lag_months", "impact_direction"]


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
    if df is None or not isinstance(df, pd.DataFrame):
        raise ValueError("df must be a non-null pandas DataFrame")
    if df.empty:
        logger.warning("build_impact_matrix: df is empty; returning empty impact matrix")
        return pd.DataFrame(columns=_IMPACT_MATRIX_COLUMNS)
    if "record_type" not in df.columns:
        raise ValueError("df must contain column 'record_type' to extract events and impact_link")

    if events is None:
        events = df[df["record_type"] == "event"].copy()
        if events.empty:
            logger.info("No event rows in df; impact matrix will have no event dates")
            events = pd.DataFrame(columns=_EVENTS_COLUMNS)
        else:
            missing = [c for c in _EVENTS_COLUMNS if c not in events.columns]
            if missing:
                raise ValueError(
                    f"Events subset is missing required columns: {missing}. "
                    f"Expected: {_EVENTS_COLUMNS}"
                )
            events = events[["record_id", "observation_date"]].copy()
    if impact_links is None:
        impact_links = df[df["record_type"] == "impact_link"].copy()
        if not impact_links.empty:
            missing = [c for c in _IMPACT_LINK_COLUMNS if c not in impact_links.columns]
            if missing:
                raise ValueError(
                    f"impact_link subset is missing required columns: {missing}. "
                    f"Expected: {_IMPACT_LINK_COLUMNS}"
                )
        elif events.empty:
            logger.info("No impact_link rows in df; returning empty impact matrix")
            return pd.DataFrame(columns=_IMPACT_MATRIX_COLUMNS)

    events = events.rename(columns={"record_id": "event_id", "observation_date": "event_date"})
    impact_links = impact_links.rename(columns={"parent_id": "event_id"})
    merge = impact_links.merge(
        events,
        on="event_id",
        how="left",
    )
    for c in _IMPACT_MATRIX_COLUMNS:
        if c not in merge.columns:
            merge[c] = pd.NA

    # Coerce event_date and drop rows with invalid dates
    merge["event_date"] = pd.to_datetime(merge["event_date"], errors="coerce")
    invalid_dates = merge["event_date"].isna()
    if invalid_dates.any():
        n_invalid = invalid_dates.sum()
        logger.warning("Dropping %d impact_link row(s) with missing or invalid event_date", n_invalid)
        merge = merge[~invalid_dates]

    result = merge[_IMPACT_MATRIX_COLUMNS].dropna(subset=["related_indicator"])
    logger.info("Built impact matrix with %d rows", len(result))
    return result


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
    if impact_matrix is None or not isinstance(impact_matrix, pd.DataFrame):
        raise ValueError("impact_matrix must be a non-null pandas DataFrame")
    required = ["related_indicator", "event_date", "lag_months", "impact_estimate", "impact_direction"]
    missing = [c for c in required if c not in impact_matrix.columns]
    if missing:
        raise ValueError(
            f"impact_matrix is missing required columns: {missing}. "
            f"Expected at least: {required}"
        )
    if not isinstance(year, int):
        raise ValueError(f"year must be an integer; got {type(year).__name__}")
    if np.isnan(base_value) or np.isinf(base_value):
        logger.warning("apply_event_impacts: base_value is %s; returning as-is", base_value)
        return base_value

    imp = impact_matrix[impact_matrix["related_indicator"] == indicator_code].copy()
    if imp.empty:
        logger.debug("No impact rows for indicator %s; returning base_value", indicator_code)
        return base_value
    imp["event_date"] = pd.to_datetime(imp["event_date"], errors="coerce")
    invalid_dates = imp["event_date"].isna()
    if invalid_dates.any():
        n_drop = invalid_dates.sum()
        logger.warning("Dropping %d row(s) with invalid event_date in apply_event_impacts", n_drop)
        imp = imp[~invalid_dates]
    if imp.empty:
        return base_value
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
        logger.debug("No effects for indicator %s in year %s; returning base_value", indicator_code, year)
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


def build_event_indicator_association_matrix(
    impact_matrix: pd.DataFrame,
    event_labels: Optional[pd.DataFrame] = None,
    indicator_codes: Optional[list[str]] = None,
    aggregate: str = "sum",
) -> pd.DataFrame:
    """
    Build the event–indicator association matrix: rows = events, columns = indicators,
    values = estimated effect (percentage points, signed).

    Parameters
    ----------
    impact_matrix : pd.DataFrame
        Output of build_impact_matrix (event_id, related_indicator, impact_estimate, impact_direction).
    event_labels : pd.DataFrame, optional
        If provided, must have columns event_id and at least one label column (e.g. indicator
        or indicator_code) to use as row index. Otherwise event_id is used.
    indicator_codes : list[str], optional
        If provided, columns are exactly these (missing cells become NaN). Otherwise
        columns are the unique related_indicator values in impact_matrix.
    aggregate : str
        How to combine multiple (event, indicator) links: "sum" or "max". Default "sum".

    Returns
    -------
    pd.DataFrame
        Rows: event_id (or event label); columns: indicator codes; values: effect in percentage points.
    """
    if impact_matrix is None or impact_matrix.empty:
        out = pd.DataFrame()
        if indicator_codes is not None:
            out = pd.DataFrame(columns=indicator_codes)
        return out
    required = ["event_id", "related_indicator", "impact_estimate", "impact_direction"]
    missing = [c for c in required if c not in impact_matrix.columns]
    if missing:
        raise ValueError(
            f"impact_matrix is missing required columns: {missing}. Expected: {required}"
        )
    mat = impact_matrix.copy()
    mat["impact_estimate"] = pd.to_numeric(mat["impact_estimate"], errors="coerce").fillna(0)
    direction = mat["impact_direction"].astype(str).str.lower()
    mat["effect_pp"] = np.where(direction.eq("decrease"), -mat["impact_estimate"], mat["impact_estimate"])
    if aggregate == "max":
        grouped = mat.groupby(["event_id", "related_indicator"], as_index=False)["effect_pp"].max()
    else:
        grouped = mat.groupby(["event_id", "related_indicator"], as_index=False)["effect_pp"].sum()
    pivot = grouped.pivot(index="event_id", columns="related_indicator", values="effect_pp")
    if event_labels is not None and not event_labels.empty and "event_id" in event_labels.columns:
        label_col = "indicator" if "indicator" in event_labels.columns else "indicator_code"
        if label_col in event_labels.columns:
            labels = event_labels.drop_duplicates("event_id").set_index("event_id")[label_col]
            pivot = pivot.reindex(labels.index)
            pivot.index = labels.values
    if indicator_codes is not None:
        for c in indicator_codes:
            if c not in pivot.columns:
                pivot[c] = np.nan
        pivot = pivot[[c for c in indicator_codes if c in pivot.columns]]
    return pivot
