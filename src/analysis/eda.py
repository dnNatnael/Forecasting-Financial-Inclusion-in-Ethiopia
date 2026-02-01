"""
EDA helpers: extract Access/Usage time series and event timeline from unified data.
"""

from typing import Optional

import pandas as pd


def get_access_series(
    df: pd.DataFrame,
    indicator_code: str = "ACC_OWNERSHIP",
    location: str = "national",
    gender: str = "all",
) -> pd.Series:
    """
    Extract national Account Ownership (or other access indicator) time series.

    Parameters
    ----------
    df : pd.DataFrame
        Unified dataframe (observations only; filter record_type if needed).
    indicator_code : str
        Default ACC_OWNERSHIP for Findex account ownership.
    location : str
        Default national.
    gender : str
        Default all.

    Returns
    -------
    pd.Series
        index = observation_date (datetime), value = value_numeric.
    """
    obs = df[(df["record_type"] == "observation") & (df["indicator_code"] == indicator_code)]
    if location:
        obs = obs[obs["location"] == location]
    if gender:
        obs = obs[obs["gender"] == gender]
    obs = obs.dropna(subset=["observation_date", "value_numeric"])
    obs = obs.sort_values("observation_date")
    # Deduplicate by date: take latest or mean if multiple (e.g. urban/rural)
    by_date = obs.groupby(pd.to_datetime(obs["observation_date"]).dt.normalize())["value_numeric"]
    return by_date.mean()


def get_usage_series(
    df: pd.DataFrame,
    indicator_code: str = "USG_DIGITAL_PAY",
    location: str = "national",
) -> pd.Series:
    """
    Extract Digital Payment Adoption (or other usage) time series.

    Parameters
    ----------
    df : pd.DataFrame
        Unified dataframe.
    indicator_code : str
        USG_DIGITAL_PAY for Findex-style digital payment adoption; fallback to USG_ACTIVE_RATE if needed.
    location : str
        Default national.

    Returns
    -------
    pd.Series
        index = observation_date, value = value_numeric.
    """
    obs = df[(df["record_type"] == "observation") & (df["indicator_code"] == indicator_code)]
    if location:
        obs = obs[obs["location"] == location]
    obs = obs.dropna(subset=["observation_date", "value_numeric"])
    obs = obs.sort_values("observation_date")
    by_date = obs.groupby(pd.to_datetime(obs["observation_date"]).dt.normalize())["value_numeric"]
    return by_date.mean()


def get_events_timeline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract events with dates for timeline viz.

    Returns
    -------
    pd.DataFrame
        Columns: record_id, category, indicator (event name), observation_date, value_text.
    """
    ev = df[df["record_type"] == "event"].copy()
    ev["observation_date"] = pd.to_datetime(ev["observation_date"])
    return ev[["record_id", "category", "indicator", "observation_date", "value_text"]].sort_values("observation_date")
