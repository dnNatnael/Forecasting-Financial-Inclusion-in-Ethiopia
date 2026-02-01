"""
Load Ethiopia financial inclusion unified dataset and reference codes.

Unified data lives in data/raw/ethiopia_fi_unified_data.xlsx with two sheets:
- ethiopia_fi_unified_data: observations, events, targets
- Impact_sheet: impact_link records (event -> indicator relationships)
"""

from pathlib import Path
from typing import Optional

import pandas as pd


def _data_dir() -> Path:
    """Project data directory (raw)."""
    return Path(__file__).resolve().parents[2] / "data" / "raw"


def load_unified_data(
    path: Optional[Path] = None,
    include_impact: bool = True,
) -> pd.DataFrame:
    """
    Load the unified financial inclusion dataset and optionally merge impact links.

    Parameters
    ----------
    path : Path, optional
        Path to ethiopia_fi_unified_data.xlsx. Defaults to data/raw.
    include_impact : bool, default True
        If True, append Impact_sheet (impact_link records) to the main sheet.

    Returns
    -------
    pd.DataFrame
        One dataframe with record_type in {observation, event, target, impact_link}.
    """
    path = path or (_data_dir() / "ethiopia_fi_unified_data.xlsx")
    main = pd.read_excel(path, sheet_name="ethiopia_fi_unified_data")
    if not include_impact:
        return main

    impact = pd.read_excel(path, sheet_name="Impact_sheet")
    if "parent_id" not in main.columns:
        main = main.assign(parent_id=pd.NA)
    return pd.concat([main, impact], ignore_index=True)


def load_reference_codes(path: Optional[Path] = None) -> dict[str, pd.DataFrame]:
    """
    Load reference_codes.xlsx (all sheets) as a dict of DataFrames.

    Returns
    -------
    dict[str, pd.DataFrame]
        Keys are sheet names (e.g. 'reference_codes'), values are DataFrames.
    """
    path = path or (_data_dir() / "reference_codes.xlsx")
    return pd.read_excel(path, sheet_name=None)
