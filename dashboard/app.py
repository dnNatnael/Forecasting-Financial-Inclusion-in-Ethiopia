"""
Interactive dashboard for Ethiopia financial inclusion forecasting.

Run: python -m dashboard.app  (from project root)
Or:  python dashboard/app.py
"""

from pathlib import Path

import dash
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html

# Add project root to path
ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))

from src.data import load_unified_data, enrich_unified_data
from src.analysis import get_access_series, get_usage_series, get_events_timeline
from src.models import forecast_access_usage, build_impact_matrix


def build_app():
    df = load_unified_data()
    df = enrich_unified_data(df)

    access_hist = get_access_series(df)
    usage_hist = get_usage_series(df)
    events = get_events_timeline(df)
    impact_matrix = build_impact_matrix(df)
    access_forecast, usage_forecast = forecast_access_usage(df)

    # Historical + forecast for Access
    acc_hist_df = pd.DataFrame({
        "year": access_hist.index.year,
        "value": access_hist.values,
        "source": "Historical (Findex + enriched)",
    })
    acc_fc_df = access_forecast[["year", "value_adjusted"]].rename(columns={"value_adjusted": "value"})
    acc_fc_df["source"] = "Forecast (trend + event impact)"
    acc_combined = pd.concat([
        acc_hist_df[["year", "value", "source"]],
        acc_fc_df[["year", "value", "source"]],
    ], ignore_index=True)

    # Historical + forecast for Usage
    use_hist_df = pd.DataFrame({
        "year": usage_hist.index.year,
        "value": usage_hist.values,
        "source": "Historical (Findex + enriched)",
    })
    use_fc_df = usage_forecast[["year", "value_adjusted"]].rename(columns={"value_adjusted": "value"})
    use_fc_df["source"] = "Forecast (trend + event impact)"
    use_combined = pd.concat([
        use_hist_df[["year", "value", "source"]],
        use_fc_df[["year", "value", "source"]],
    ], ignore_index=True)

    # Targets (NFIS-II)
    targets = df[df["record_type"] == "target"]
    acc_target = targets[targets["indicator_code"] == "ACC_OWNERSHIP"]
    target_2025 = acc_target[acc_target["observation_date"].dt.year == 2025]["value_numeric"].values
    target_val = float(target_2025[0]) if len(target_2025) else None

    fig_access = go.Figure()
    hist = acc_combined[acc_combined["source"].str.contains("Historical")]
    fc = acc_combined[acc_combined["source"].str.contains("Forecast")]
    fig_access.add_trace(
        go.Scatter(x=hist["year"], y=hist["value"], mode="lines+markers", name="Historical", line=dict(color="#1f77b4"))
    )
    fig_access.add_trace(
        go.Scatter(x=fc["year"], y=fc["value"], mode="lines+markers", name="Forecast", line=dict(color="#ff7f0e", dash="dash"))
    )
    if target_val is not None:
        fig_access.add_hline(y=target_val, line_dash="dot", line_color="gray", annotation_text=f"NFIS-II target {target_val}%")
    fig_access.update_layout(
        title="Access: Account Ownership Rate (%)",
        xaxis_title="Year",
        yaxis_title="% of adults (15+)",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    fig_usage = go.Figure()
    hist_u = use_combined[use_combined["source"].str.contains("Historical")]
    fc_u = use_combined[use_combined["source"].str.contains("Forecast")]
    fig_usage.add_trace(
        go.Scatter(x=hist_u["year"], y=hist_u["value"], mode="lines+markers", name="Historical", line=dict(color="#2ca02c"))
    )
    fig_usage.add_trace(
        go.Scatter(x=fc_u["year"], y=fc_u["value"], mode="lines+markers", name="Forecast", line=dict(color="#d62728", dash="dash"))
    )
    fig_usage.update_layout(
        title="Usage: Digital Payment Adoption Rate (%)",
        xaxis_title="Year",
        yaxis_title="% of adults (past 12 months)",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    # Event timeline (bar or table)
    events_display = events.copy()
    events_display["date"] = events_display["observation_date"].dt.strftime("%Y-%m-%d")
    events_display = events_display[["date", "category", "indicator", "value_text"]]

    app = dash.Dash(__name__, title="Ethiopia Financial Inclusion Forecast")
    app.layout = html.Div(
        [
            html.H1("Ethiopia Financial Inclusion Forecasting", style={"textAlign": "center"}),
            html.P(
                "Selam Analytics — Access (Account Ownership) and Usage (Digital Payment Adoption), 2025–2027.",
                style={"textAlign": "center", "color": "#666"},
            ),
            html.Hr(),
            html.Div(
                [
                    html.Div(
                        [
                            dcc.Graph(figure=fig_access, id="fig-access"),
                        ],
                        style={"width": "48%", "display": "inline-block", "padding": "10px"},
                    ),
                    html.Div(
                        [
                            dcc.Graph(figure=fig_usage, id="fig-usage"),
                        ],
                        style={"width": "48%", "display": "inline-block", "padding": "10px"},
                    ),
                ],
            ),
            html.H3("Forecast summary (2025–2027)"),
            html.Div(
                [
                    html.Div(
                        [
                            html.H4("Access (Account Ownership %)"),
                            html.Table(
                                [
                                    html.Tr([html.Th("Year"), html.Th("Forecast (%)")]),
                                    *[html.Tr([html.Td(r["year"]), html.Td(f"{r['value_adjusted']:.1f}")]) for _, r in access_forecast.iterrows()],
                                ],
                                style={"margin": "10px"},
                            ),
                        ],
                        style={"width": "30%", "display": "inline-block", "verticalAlign": "top"},
                    ),
                    html.Div(
                        [
                            html.H4("Usage (Digital Payment Adoption %)"),
                            html.Table(
                                [
                                    html.Tr([html.Th("Year"), html.Th("Forecast (%)")]),
                                    *[html.Tr([html.Td(r["year"]), html.Td(f"{r['value_adjusted']:.1f}")]) for _, r in usage_forecast.iterrows()],
                                ],
                                style={"margin": "10px"},
                            ),
                        ],
                        style={"width": "30%", "display": "inline-block", "verticalAlign": "top"},
                    ),
                ],
            ),
            html.H3("Events timeline"),
            html.Div(
                [
                    html.Table(
                        [html.Tr([html.Th("Date"), html.Th("Category"), html.Th("Event"), html.Th("Status")])]
                        + [html.Tr([html.Td(r["date"]), html.Td(r["category"]), html.Td(r["indicator"]), html.Td(r["value_text"] or "")]) for _, r in events_display.iterrows()],
                        style={"border": "1px solid #ddd", "borderCollapse": "collapse", "margin": "10px"},
                    ),
                ],
            ),
            html.Hr(),
            html.Footer(
                "Data: Global Findex, NBE, operators; forecasts combine trend and event-impact model. Not official NBE/World Bank projections.",
                style={"textAlign": "center", "fontSize": "12px", "color": "#888"},
            ),
        ],
        style={"fontFamily": "system-ui, sans-serif", "maxWidth": "1200px", "margin": "0 auto", "padding": "20px"},
    )
    return app


app = build_app()
server = app.server

if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
