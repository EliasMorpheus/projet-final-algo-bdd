from __future__ import annotations

from pathlib import Path
import sys

import dash
from dash import Input, Output, dcc, html
import mysql.connector
import pandas as pd
import plotly.express as px


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR / "python"))

from config import load_db_config  # noqa: E402


def query_dataframe(query: str) -> pd.DataFrame:
    with mysql.connector.connect(**load_db_config()) as connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query)
        return pd.DataFrame(cursor.fetchall())


def load_dashboard_data() -> pd.DataFrame:
    return query_dataframe(
        """
        SELECT
            r.customer_id,
            r.recency_days,
            r.frequency_orders,
            r.monetary_value,
            r.rfm_score,
            r.segment,
            r.city,
            c.acquisition_channel
        FROM rfm_scores r
        JOIN customers c ON c.customer_id = r.customer_id
        """
    )


df = load_dashboard_data()
segments = sorted(df["segment"].unique())

app = dash.Dash(__name__, assets_folder=str(ROOT_DIR / "assets"))
app.title = "Dashboard RFM Marketing"

app.layout = html.Div(
    className="page",
    children=[
        html.Div(
            className="header",
            children=[
                html.Div(
                    [
                        html.H1("Segmentation client e-commerce"),
                        html.P("Analyse RFM, valeur client et activation marketing"),
                    ]
                ),
                html.Div(
                    className="filter",
                    children=[
                        html.Label("Segment"),
                        dcc.Dropdown(
                            id="segment-filter",
                            options=[{"label": "Tous les segments", "value": "all"}]
                            + [{"label": segment, "value": segment} for segment in segments],
                            value="all",
                            clearable=False,
                        ),
                    ],
                ),
            ],
        ),
        html.Div(
            className="kpi-grid",
            children=[
                html.Div([html.Span("Clients"), html.Strong(id="kpi-clients")], className="kpi"),
                html.Div([html.Span("CA total"), html.Strong(id="kpi-revenue")], className="kpi"),
                html.Div([html.Span("Panier moyen client"), html.Strong(id="kpi-average")], className="kpi"),
            ],
        ),
        html.Div(
            className="charts",
            children=[
                dcc.Graph(id="segment-chart", config={"displayModeBar": False}),
                dcc.Graph(id="city-chart", config={"displayModeBar": False}),
                dcc.Graph(id="channel-chart", config={"displayModeBar": False}),
            ],
        ),
    ],
)


@app.callback(
    Output("kpi-clients", "children"),
    Output("kpi-revenue", "children"),
    Output("kpi-average", "children"),
    Output("segment-chart", "figure"),
    Output("city-chart", "figure"),
    Output("channel-chart", "figure"),
    Input("segment-filter", "value"),
)
def update_dashboard(selected_segment: str):
    filtered = df if selected_segment == "all" else df[df["segment"] == selected_segment]

    clients = filtered["customer_id"].nunique()
    revenue = filtered["monetary_value"].sum()
    average = revenue / clients if clients else 0

    segment_fig = px.bar(
        filtered.groupby("segment", as_index=False)
        .agg(customers=("customer_id", "nunique"), revenue=("monetary_value", "sum"))
        .sort_values("customers", ascending=False),
        x="segment",
        y="customers",
        color="segment",
        title="Nombre de clients par segment",
    )

    city_fig = px.bar(
        filtered.groupby("city", as_index=False)
        .agg(revenue=("monetary_value", "sum"))
        .sort_values("revenue", ascending=False)
        .head(10),
        x="city",
        y="revenue",
        title="Chiffre d'affaires par ville",
    )

    channel_fig = px.pie(
        filtered.groupby("acquisition_channel", as_index=False)
        .agg(revenue=("monetary_value", "sum")),
        names="acquisition_channel",
        values="revenue",
        title="Revenu par canal d'acquisition",
        hole=0.45,
    )

    for figure in (segment_fig, city_fig, channel_fig):
        figure.update_layout(
            template="plotly_white",
            margin=dict(l=30, r=20, t=55, b=40),
            legend_title_text="",
            font=dict(family="Arial", size=13),
        )

    return (
        f"{clients}",
        f"{revenue:,.0f} EUR".replace(",", " "),
        f"{average:,.0f} EUR".replace(",", " "),
        segment_fig,
        city_fig,
        channel_fig,
    )


if __name__ == "__main__":
    app.run_server(debug=False, host="127.0.0.1", port=8050)
