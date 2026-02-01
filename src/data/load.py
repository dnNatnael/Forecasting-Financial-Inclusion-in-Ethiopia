"""
Load Ethiopia financial inclusion unified dataset, reference codes, and guide.

Supports:
- ethiopia_fi_unified_data.xlsx (Sheet 1: data; Sheet 2: impact_links)
- ethiopia_fi_unified_data.csv (single file with all record_types; impact rows have parent_id)
"""

from pathlib import Path
from typing import Optional, Union

import pandas as pd


def _data_dir() -> Path:
    """Project data directory (raw)."""
    return Path(__file__).resolve().parents[2] / "data" / "raw"


def load_unified_data(
    path: Optional[Union[Path, str]] = None,
    include_impact: bool = True,
) -> pd.DataFrame:
    """
    Load the unified financial inclusion dataset (and optionally impact links).

    Accepts:
    - .xlsx: Sheet "ethiopia_fi_unified_data" (data) + Sheet "Impact_sheet" (impact_links)
    - .csv: Single file with all record_types; impact_link rows have parent_id

    Parameters
    ----------
    path : Path or str, optional
        Path to ethiopia_fi_unified_data.xlsx or .csv. Defaults to data/raw.
    include_impact : bool, default True
        If True, include impact_link records (xlsx: merge Impact_sheet; csv: already combined).

    Returns
    -------
    pd.DataFrame
        One dataframe with record_type in {observation, event, target, impact_link}.
    """
    raw_dir = _data_dir()
    path = path or raw_dir / "ethiopia_fi_unified_data.xlsx"
    path = Path(path)

    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
        if not include_impact and "record_type" in df.columns:
            df = df[df["record_type"] != "impact_link"].copy()
        return df

    main = pd.read_excel(path, sheet_name="ethiopia_fi_unified_data")
    if not include_impact:
        return main
    impact = pd.read_excel(path, sheet_name="Impact_sheet")
    if "parent_id" not in main.columns:
        main = main.assign(parent_id=pd.NA)
    return pd.concat([main, impact], ignore_index=True)


def load_reference_codes(path: Optional[Union[Path, str]] = None) -> dict[str, pd.DataFrame]:
    """
    Load reference_codes.xlsx (all sheets) as a dict of DataFrames.

    Returns
    -------
    dict[str, pd.DataFrame]
        Keys are sheet names (e.g. 'reference_codes'), values are DataFrames.
    """
    path = path or (_data_dir() / "reference_codes.xlsx")
    return pd.read_excel(path, sheet_name=None)


def load_guide(path: Optional[Union[Path, str]] = None) -> dict[str, pd.DataFrame]:
    """
    Load Additional Data Points Guide.xlsx (all sheets).

    Sheets: A. Alternative Baselines, B. Direct Corrln, C. Indirect Corrln, D. Market Nuances.

    Returns
    -------
    dict[str, pd.DataFrame]
        Keys are sheet names, values are DataFrames.
    """
    path = path or (_data_dir() / "Additional Data Points Guide.xlsx")
    return pd.read_excel(path, sheet_name=None)
