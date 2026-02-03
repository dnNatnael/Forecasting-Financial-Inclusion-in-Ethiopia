"""
Interactive dashboard for Ethiopia financial inclusion forecasting.

Run from project root:
  python -m dashboard.app
  python dashboard/app.py

Includes: overview metric cards, date-range and channel comparison,
scenario/model selectors, inclusion projections with target progress,
and event-impact comparison view.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import dash
from dash import dcc, html, Input, Output, callback

from src.data import load_unified_data, enrich_unified_data
from src.analysis import get_access_series, get_usage_series, get_events_timeline
from src.models import (
    forecast_access_usage,
    forecast_access_usage_with_uncertainty,
    build_impact_matrix,
    build_event_indicator_association_matrix,
)


def get_indicator_series(df: pd.DataFrame, indicator_code: str) -> pd.Series:
    """Time series for any indicator (channel comparison)."""
    obs = df[(df["record_type"] == "observation") & (df["indicator_code"] == indicator_code)]
    obs = obs.dropna(subset=["observation_date", "value_numeric"]).sort_values("observation_date")
    if obs.empty:
        return pd.Series(dtype=float)
    by_date = obs.groupby(pd.to_datetime(obs["observation_date"]).dt.normalize())["value_numeric"]
    return by_date.mean()


# ----- Load data once -----
_df = None
_events = None
_impact_matrix = None
_assoc_matrix = None
_access_hist = None
_usage_hist = None
_access_forecast = None
_usage_forecast = None
_access_fu = None
_usage_fu = None
_target_val = None
_years_avail = None
_indicator_codes = None


def _load():
    global _df, _events, _impact_matrix, _assoc_matrix
    global _access_hist, _usage_hist, _access_forecast, _usage_forecast, _access_fu, _usage_fu
    global _target_val, _years_avail, _indicator_codes
    if _df is not None:
        return
    _df = load_unified_data()
    _df = enrich_unified_data(_df)
    _access_hist = get_access_series(_df)
    _usage_hist = get_usage_series(_df)
    _events = get_events_timeline(_df)
    _impact_matrix = build_impact_matrix(_df)
    _access_forecast, _usage_forecast = forecast_access_usage(_df)
    _access_fu, _usage_fu = forecast_access_usage_with_uncertainty(_df, forecast_years=[2025, 2026, 2027])
    targets = _df[_df["record_type"] == "target"]
    acc_target = targets[targets["indicator_code"] == "ACC_OWNERSHIP"] if not targets.empty else pd.DataFrame()
    target_2025 = acc_target[acc_target["observation_date"].dt.year == 2025]["value_numeric"].values
    _target_val = float(target_2025[0]) if len(target_2025) else 60.0
    obs = _df[_df["record_type"] == "observation"]
    obs["observation_date"] = pd.to_datetime(obs["observation_date"])
    _years_avail = sorted(obs["observation_date"].dt.year.dropna().astype(int).unique().tolist())
    _indicator_codes = sorted(obs["indicator_code"].dropna().unique().tolist())
    if not _impact_matrix.empty:
        events_with_label = _df[_df["record_type"] == "event"][["record_id", "indicator"]].rename(columns={"record_id": "event_id"})
        _assoc_matrix = build_event_indicator_association_matrix(_impact_matrix, event_labels=events_with_label)
    else:
        _assoc_matrix = pd.DataFrame()


_load()


def _build_event_impact_figure():
    if _assoc_matrix.empty:
        return go.Figure().update_layout(template="plotly_white", title="No event–indicator impact data available")
    fig = px.imshow(
        _assoc_matrix.fillna(0),
        labels=dict(x="Indicator", y="Event", color="Effect (pp)"),
        x=_assoc_matrix.columns.tolist(),
        y=_assoc_matrix.index.tolist(),
        color_continuous_scale="RdBu",
        color_continuous_midpoint=0,
        aspect="auto",
    )
    fig.update_layout(
        title="Event–indicator impact (percentage points)",
        template="plotly_white",
        xaxis_tickangle=-45,
        height=max(400, len(_assoc_matrix) * 50),
    )
    return fig


def _build_events_table():
    ev = _events.copy()
    ev["date"] = ev["observation_date"].dt.strftime("%Y-%m-%d")
    rows = [html.Tr([html.Th("Date"), html.Th("Category"), html.Th("Event"), html.Th("Status")])]
    for _, r in ev.iterrows():
        rows.append(html.Tr([html.Td(r["date"]), html.Td(r["category"]), html.Td(r["indicator"]), html.Td(r.get("value_text") or "")]))
    return html.Table(rows, style={"border": "1px solid #ddd", "borderCollapse": "collapse", "margin": "10px", "width": "100%"})


# ----- Metric card style -----
CARD_STYLE = {
    "border": "1px solid #e0e0e0",
    "borderRadius": "8px",
    "padding": "16px",
    "textAlign": "center",
    "boxShadow": "0 1px 3px rgba(0,0,0,0.08)",
    "backgroundColor": "#fafafa",
}
CARD_TITLE = {"fontSize": "12px", "color": "#666", "marginBottom": "4px"}
CARD_VALUE = {"fontSize": "24px", "fontWeight": "bold", "color": "#333"}

# ----- Build app -----
app = dash.Dash(__name__, title="Ethiopia Financial Inclusion Forecast")

# Overview metric cards
last_acc = float(_access_hist.iloc[-1]) if not _access_hist.empty else None
last_use = float(_usage_hist.iloc[-1]) if not _usage_hist.empty else None
access_growth = None
if not _access_hist.empty and len(_access_hist) >= 2:
    v0, v1 = _access_hist.iloc[0], _access_hist.iloc[-1]
    access_growth = (float(v1) - float(v0)) / max(float(v0), 1e-6) * 100
proj_2027 = float(_access_fu["value_adjusted"].iloc[-1]) if len(_access_fu) else last_acc
target_gap = (_target_val - proj_2027) if _target_val and proj_2027 is not None else None

app.layout = html.Div(
    [
        html.H1("Ethiopia Financial Inclusion Forecasting", style={"textAlign": "center"}),
        html.P(
            "Selam Analytics — Access (Account Ownership) and Usage (Digital Payment Adoption), 2025–2027.",
            style={"textAlign": "center", "color": "#666"},
        ),
        html.Hr(),
        # ----- Overview: metric cards -----
        html.H3("Overview"),
        html.Div(
            [
                html.Div(
                    [
                        html.Div("Account ownership (latest)", style=CARD_TITLE),
                        html.Div(f"{last_acc:.1f}%" if last_acc is not None else "—", style=CARD_VALUE),
                    ],
                    style={**CARD_STYLE, "width": "24%", "display": "inline-block", "marginRight": "4px"},
                ),
                html.Div(
                    [
                        html.Div("Digital payment adoption (latest)", style=CARD_TITLE),
                        html.Div(f"{last_use:.1f}%" if last_use is not None else "—", style=CARD_VALUE),
                    ],
                    style={**CARD_STYLE, "width": "24%", "display": "inline-block", "marginRight": "4px"},
                ),
                html.Div(
                    [
                        html.Div("Access growth (period)", style=CARD_TITLE),
                        html.Div(
                            f"{access_growth:.1f}%" if access_growth is not None else "—",
                            style=CARD_VALUE,
                        ),
                    ],
                    style={**CARD_STYLE, "width": "24%", "display": "inline-block", "marginRight": "4px"},
                ),
                html.Div(
                    [
                        html.Div("Gap to target (2027 proj.)", style=CARD_TITLE),
                        html.Div(
                            f"{target_gap:+.1f} pp" if target_gap is not None else "—",
                            style={**CARD_VALUE, "color": "#c0392b" if target_gap and target_gap > 0 else "#27ae60"},
                        ),
                    ],
                    style={**CARD_STYLE, "width": "24%", "display": "inline-block"},
                ),
            ],
            style={"marginBottom": "24px"},
        ),
        # ----- Trends: date-range and channel comparison -----
        html.H3("Trends"),
        html.Div(
            [
                html.Div(
                    [
                        html.Label("Date range (year)", style={"display": "block", "marginBottom": "4px"}),
                        dcc.RangeSlider(
                            id="date-range",
                            min=min(_years_avail) if _years_avail else 2010,
                            max=max(_years_avail) if _years_avail else 2027,
                            step=1,
                            value=[min(_years_avail) if _years_avail else 2010, max(_years_avail) if _years_avail else 2027],
                            marks={y: str(y) for y in (_years_avail if len(_years_avail) <= 15 else [min(_years_avail), max(_years_avail)])},
                        ),
                    ],
                    style={"width": "48%", "display": "inline-block", "verticalAlign": "top", "marginBottom": "12px"},
                ),
                html.Div(
                    [
                        html.Label("Channel comparison (indicators)", style={"display": "block", "marginBottom": "4px"}),
                        dcc.Dropdown(
                            id="channel-indicators",
                            options=[{"label": c, "value": c} for c in _indicator_codes],
                            value=_indicator_codes[:4] if _indicator_codes else None,
                            multi=True,
                            placeholder="Select indicators",
                        ),
                    ],
                    style={"width": "48%", "display": "inline-block", "verticalAlign": "top", "marginBottom": "12px"},
                ),
            ],
        ),
        dcc.Graph(id="trend-graph"),
        # ----- Forecasts: scenario and model selectors -----
        html.H3("Forecasts"),
        html.Div(
            [
                html.Div(
                    [
                        html.Label("Scenario", style={"display": "block", "marginBottom": "4px"}),
                        dcc.RadioItems(
                            id="forecast-scenario",
                            options=[
                                {"label": "Optimistic", "value": "optimistic"},
                                {"label": "Base", "value": "base"},
                                {"label": "Pessimistic", "value": "pessimistic"},
                            ],
                            value="base",
                            inline=True,
                        ),
                    ],
                    style={"width": "32%", "display": "inline-block", "marginRight": "12px"},
                ),
                html.Div(
                    [
                        html.Label("Model / view", style={"display": "block", "marginBottom": "4px"}),
                        dcc.RadioItems(
                            id="forecast-model",
                            options=[
                                {"label": "Base (trend + event impact)", "value": "base"},
                                {"label": "With confidence intervals", "value": "ci"},
                            ],
                            value="base",
                            inline=True,
                        ),
                    ],
                    style={"width": "32%", "display": "inline-block"},
                ),
            ],
            style={"marginBottom": "12px"},
        ),
        html.Div(
            [
                html.Div([dcc.Graph(id="forecast-access")], style={"width": "48%", "display": "inline-block", "padding": "8px"}),
                html.Div([dcc.Graph(id="forecast-usage")], style={"width": "48%", "display": "inline-block", "padding": "8px"}),
            ],
        ),
        html.H4("Key projected milestones"),
        html.Div(id="forecast-table-container"),
        # ----- Inclusion projections with target progress -----
        html.Hr(),
        html.H3("Inclusion Projections"),
        html.P("Progress toward account ownership target and projected path.", style={"color": "#666"}),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(f"Target: {_target_val:.0f}%", style=CARD_TITLE),
                        html.Div(id="inclusion-proj-value", style=CARD_VALUE),
                    ],
                    style={**CARD_STYLE, "width": "30%", "display": "inline-block", "marginRight": "12px"},
                ),
                html.Div(
                    [
                        html.Div("Progress toward target (2027)", style=CARD_TITLE),
                        dcc.Slider(
                            id="inclusion-scenario",
                            min=0,
                            max=2,
                            step=1,
                            value=1,
                            marks={0: "Pessimistic", 1: "Base", 2: "Optimistic"},
                        ),
                    ],
                    style={**CARD_STYLE, "width": "65%", "display": "inline-block", "padding": "16px"},
                ),
            ],
            style={"marginBottom": "16px"},
        ),
        html.Div(id="inclusion-progress-bar", style={"marginBottom": "12px"}),
        dcc.Graph(id="inclusion-projection-graph"),
        # ----- Event-impact comparison view -----
        html.Hr(),
        html.H3("Event–Impact Comparison"),
        html.P(
            "Estimated effect (percentage points) of each event on each indicator. Positive = increase, negative = decrease.",
            style={"color": "#666"},
        ),
        dcc.Graph(id="event-impact-heatmap", figure=_build_event_impact_figure()),
        # ----- Events timeline -----
        html.H3("Events timeline"),
        html.Div(_build_events_table()),
        html.Hr(),
        html.Footer(
            "Data: Global Findex, NBE, operators; forecasts combine trend and event-impact model. Not official NBE/World Bank projections.",
            style={"textAlign": "center", "fontSize": "12px", "color": "#888"},
        ),
    ],
    style={"fontFamily": "system-ui, sans-serif", "maxWidth": "1200px", "margin": "0 auto", "padding": "20px"},
)


@callback(
    Output("trend-graph", "figure"),
    Input("date-range", "value"),
    Input("channel-indicators", "value"),
)
def update_trend_graph(date_range, channel_indicators):
    if not date_range or not channel_indicators:
        return go.Figure().update_layout(template="plotly_white", title="Select date range and at least one indicator")
    y_min, y_max = date_range[0], date_range[1]
    fig = go.Figure()
    for code in channel_indicators:
        ser = get_indicator_series(_df, code)
        if ser.empty:
            continue
        years = ser.index.year
        x = [int(y) for y in years if y_min <= y <= y_max]
        y_vals = [float(ser.iloc[i]) for i, y in enumerate(years) if y_min <= y <= y_max]
        if not x:
            continue
        fig.add_trace(go.Scatter(x=x, y=y_vals, mode="lines+markers", name=code))
    fig.update_layout(
        title="Time series by indicator (channel comparison)",
        xaxis_title="Year",
        yaxis_title="Value",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


@callback(
    Output("forecast-access", "figure"),
    Output("forecast-usage", "figure"),
    Input("forecast-scenario", "value"),
    Input("forecast-model", "value"),
)
def update_forecast_graphs(scenario, model):
    acc_hist_df = pd.DataFrame({"year": _access_hist.index.year, "value": _access_hist.values})
    use_hist_df = pd.DataFrame({"year": _usage_hist.index.year, "value": _usage_hist.values})
    show_ci = model == "ci"
    acc_vals = _access_fu["scenario_optimistic"] if scenario == "optimistic" else _access_fu["scenario_pessimistic"] if scenario == "pessimistic" else _access_fu["scenario_base"]
    use_vals = _usage_fu["scenario_optimistic"] if scenario == "optimistic" else _usage_fu["scenario_pessimistic"] if scenario == "pessimistic" else _usage_fu["scenario_base"]
    fig_acc = go.Figure()
    fig_acc.add_trace(go.Scatter(x=acc_hist_df["year"], y=acc_hist_df["value"], mode="lines+markers", name="Historical", line=dict(color="#1f77b4")))
    fig_acc.add_trace(go.Scatter(x=_access_fu["year"], y=acc_vals, mode="lines+markers", name="Forecast", line=dict(color="#ff7f0e", dash="dash")))
    if show_ci and "ci_lower" in _access_fu.columns:
        fig_acc.add_trace(go.Scatter(x=_access_fu["year"], y=_access_fu["ci_upper"], fill=None, mode="lines", line=dict(width=0), showlegend=False))
        fig_acc.add_trace(go.Scatter(x=_access_fu["year"], y=_access_fu["ci_lower"], fill="tonexty", mode="lines", name="95% CI", line=dict(width=0)))
    fig_acc.add_hline(y=_target_val, line_dash="dot", line_color="gray", annotation_text=f"Target {_target_val:.0f}%")
    fig_acc.update_layout(title="Access: Account Ownership (%)", xaxis_title="Year", yaxis_title="%", template="plotly_white")
    fig_use = go.Figure()
    fig_use.add_trace(go.Scatter(x=use_hist_df["year"], y=use_hist_df["value"], mode="lines+markers", name="Historical", line=dict(color="#2ca02c")))
    fig_use.add_trace(go.Scatter(x=_usage_fu["year"], y=use_vals, mode="lines+markers", name="Forecast", line=dict(color="#d62728", dash="dash")))
    if show_ci and "ci_lower" in _usage_fu.columns:
        fig_use.add_trace(go.Scatter(x=_usage_fu["year"], y=_usage_fu["ci_upper"], fill=None, mode="lines", line=dict(width=0), showlegend=False))
        fig_use.add_trace(go.Scatter(x=_usage_fu["year"], y=_usage_fu["ci_lower"], fill="tonexty", mode="lines", name="95% CI", line=dict(width=0)))
    fig_use.update_layout(title="Usage: Digital Payment Adoption (%)", xaxis_title="Year", yaxis_title="%", template="plotly_white")
    return fig_acc, fig_use


@callback(
    Output("forecast-table-container", "children"),
    Input("forecast-scenario", "value"),
)
def update_forecast_table(scenario):
    acc_vals = _access_fu["scenario_optimistic"] if scenario == "optimistic" else _access_fu["scenario_pessimistic"] if scenario == "pessimistic" else _access_fu["scenario_base"]
    use_vals = _usage_fu["scenario_optimistic"] if scenario == "optimistic" else _usage_fu["scenario_pessimistic"] if scenario == "pessimistic" else _usage_fu["scenario_base"]
    rows = [
        html.Tr([html.Th("Year"), html.Th("Access (%)"), html.Th("Usage (%)")]),
        *[html.Tr([html.Td(int(y)), html.Td(f"{acc_vals.iloc[i]:.1f}"), html.Td(f"{use_vals.iloc[i]:.1f}")]) for i, y in enumerate(_access_fu["year"])],
    ]
    return html.Table(rows, style={"border": "1px solid #ddd", "borderCollapse": "collapse", "padding": "8px"})


@callback(
    Output("inclusion-proj-value", "children"),
    Output("inclusion-progress-bar", "children"),
    Output("inclusion-projection-graph", "figure"),
    Input("inclusion-scenario", "value"),
)
def update_inclusion(slider_val):
    scenario = ["pessimistic", "base", "optimistic"][slider_val]
    acc_vals = _access_fu["scenario_pessimistic"] if scenario == "pessimistic" else _access_fu["scenario_base"] if scenario == "base" else _access_fu["scenario_optimistic"]
    use_vals = _usage_fu["scenario_pessimistic"] if scenario == "pessimistic" else _usage_fu["scenario_base"] if scenario == "base" else _usage_fu["scenario_optimistic"]
    proj_2027 = float(acc_vals.iloc[-1])
    pct = min(1.0, max(0.0, proj_2027 / _target_val)) if _target_val else 0
    progress_bar = html.Div(
        [
            html.Div(
                f"{pct*100:.0f}% of target",
                style={
                    "width": f"{pct*100}%",
                    "height": "28px",
                    "backgroundColor": "#3498db",
                    "borderRadius": "4px",
                    "color": "white",
                    "display": "flex",
                    "alignItems": "center",
                    "paddingLeft": "8px",
                    "fontSize": "14px",
                },
            ),
        ],
        style={"width": "100%", "backgroundColor": "#ecf0f1", "borderRadius": "4px", "overflow": "hidden"},
    )
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=_access_fu["year"], y=acc_vals, mode="lines+markers", name="Access (projected)", line=dict(color="#2980b9")))
    fig.add_trace(go.Scatter(x=_usage_fu["year"], y=use_vals, mode="lines+markers", name="Usage (projected)", line=dict(color="#27ae60")))
    fig.add_hline(y=_target_val, line_dash="dot", line_color="gray", annotation_text=f"Target {_target_val:.0f}%")
    fig.update_layout(title=f"Inclusion projections — {scenario.capitalize()} scenario", xaxis_title="Year", yaxis_title="%", template="plotly_white")
    return f"{proj_2027:.1f}% (2027)", progress_bar, fig


server = app.server

if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
