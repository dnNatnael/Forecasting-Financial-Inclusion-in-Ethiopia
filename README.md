# Forecasting Financial Inclusion in Ethiopia

Selam Analytics — forecasting system for **Access** (Account Ownership) and **Usage** (Digital Payment Adoption) in Ethiopia, aligned with the World Bank Global Findex framework.

## Overview

- **Access**: Share of adults (15+) with an account at a financial institution or using mobile money (past 12 months).
- **Usage**: Share of adults who made or received a digital payment (past 12 months).

The system:

1. **Loads and enriches** the unified financial inclusion dataset (observations, events, targets, impact links).
2. **Analyzes** patterns and event–indicator relationships.
3. **Models** how events (product launches, policy, infrastructure) affect inclusion via `impact_link` records.
4. **Forecasts** Access and Usage for 2025–2027 (trend + event-impact adjustments).
5. **Presents** results in an interactive dashboard.

## Data

- **Unified dataset**: `data/raw/ethiopia_fi_unified_data.xlsx`
  - Sheet **ethiopia_fi_unified_data**: `observation`, `event`, `target`.
  - Sheet **Impact_sheet**: `impact_link` (event → indicator effects, lag, magnitude).
- **Reference codes**: `data/raw/reference_codes.xlsx`.
- **Enrichment guide**: `data/raw/Additional Data Points Guide.xlsx` (alternative baselines, direct/indirect indicators, market nuances).

Enrichment (Task 1) adds:

- 2011 Account Ownership (14%) for continuity.
- Digital Payment Adoption Rate (Usage) for 2021 and 2024.
- Placeholder structure for direct/indirect indicators (agent density, ATM/branch density, smartphone penetration, mobile internet) to be filled from IMF FAS, GSMA, ITU, NBE.

## Setup

```bash
# From project root; use a virtual environment if possible
python3 -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Dependencies include `pandas`, `openpyxl`, `numpy`, `scikit-learn`, `statsmodels`, `dash`, `plotly`, and `python-docx` for report generation.

## Usage

### Load and enrich data

```python
from src.data import load_unified_data, load_reference_codes, enrich_unified_data

df = load_unified_data()       # main sheet + Impact_sheet
ref = load_reference_codes()   # reference_codes.xlsx
df = enrich_unified_data(df)   # add Task 1 enrichment observations
```

### Access / Usage series and events

```python
from src.analysis import get_access_series, get_usage_series, get_events_timeline

access = get_access_series(df, indicator_code="ACC_OWNERSHIP")
usage  = get_usage_series(df, indicator_code="USG_DIGITAL_PAY")
events = get_events_timeline(df)
```

### Event–impact and forecast

```python
from src.models import build_impact_matrix, build_event_indicator_association_matrix, forecast_access_usage, forecast_access_usage_with_uncertainty

impact_matrix = build_impact_matrix(df)
assoc_matrix = build_event_indicator_association_matrix(impact_matrix)  # events × indicators (effect in pp)
access_forecast, usage_forecast = forecast_access_usage(df)

# With confidence intervals and scenarios (Task 4)
access_f, usage_f = forecast_access_usage_with_uncertainty(df, forecast_years=[2025, 2026, 2027])
# Returns DataFrames with value_baseline, value_adjusted, ci_lower, ci_upper, scenario_optimistic, scenario_pessimistic
```

### Dashboard

```bash
python -m dashboard.app
# or: python dashboard/app.py
```

Then open http://127.0.0.1:8050 for the interactive dashboard (Access/Usage charts, forecast table, events timeline).

### Interim Report (.docx)

To generate the Interim Report in Word format (data enrichment summary, EDA insights with visualizations, event–indicator observations, limitations, next steps):

```bash
pip install python-docx   # if not already installed
python scripts/generate_interim_report.py
```

Output: `Interim_Report.docx` in the project root; figures are saved under `report_figures/`.

## Project structure

```
├── data/raw/                    # ethiopia_fi_unified_data.xlsx, reference_codes.xlsx, guide
├── data/processed/              # enriched CSV/Excel; forecast tables (Task 4)
├── src/
│   ├── data/                    # load.py, enrichment.py
│   ├── analysis/                # eda.py (access/usage series, events)
│   └── models/                  # event_impact.py, forecast.py (with uncertainty & scenarios)
├── dashboard/app.py             # Dash app
├── notebooks/                   # 01 EDA, 02 task-2, 03 event impact, 04 forecasting (Task 4)
├── models/                      # (optional) saved models
└── tests/
```

## Methodology (summary)

- **Baseline trend**: Linear regression of historical Access/Usage on year.
- **Event impact**: `impact_link` records give `related_indicator`, `impact_estimate` (e.g. +15 pp), `lag_months`. Effects are applied in the year `event_date + lag_months` and summed for each indicator.
- **Forecast**: Baseline trend value + cumulative event effects for 2025, 2026, 2027.
- **Event–indicator matrix**: See `notebooks/03_event_impact_modeling.ipynb` and `docs/EVENT_IMPACT_METHODOLOGY.md` for the association matrix (events × indicators), validation (e.g. Telebirr vs ACC_MM_ACCOUNT), and full methodology, assumptions, and limitations.
- **Forecasting (Task 4)**: `notebooks/04_forecasting_access_usage.ipynb` produces forecasts for 2025–2027 with baseline trend, event-adjusted values, 95% confidence intervals, and optimistic/base/pessimistic scenarios; see `docs/TASK4_FORECASTING.md`. Merge `task-3` into `main` via PR before or with task-4.

## License and disclaimer

Forecasts are illustrative and not official NBE or World Bank projections. Data sources: Global Findex, NBE, operator reports, and enrichment guide.
