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
    data = query_dataframe(
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
    numeric_columns = ["recency_days", "frequency_orders", "monetary_value", "rfm_score"]
    data[numeric_columns] = data[numeric_columns].apply(pd.to_numeric)
    return data


df = load_dashboard_data()
segments = sorted(df["segment"].unique())
segment_actions = {
    "Champions": "Maintenir la relation VIP et proposer des offres exclusives.",
    "Clients fideles": "Renforcer la fidelite avec des avantages recurrents.",
    "Clients a risque": "Prioriser une campagne de reactivation personnalisee.",
    "Nouveaux clients": "Declencher une sequence d'onboarding et un second achat.",
    "Fort potentiel": "Proposer des bundles et recommandations premium.",
    "A developper": "Tester des offres decouverte et contenus educatifs.",
}
segment_order = [
    "Champions",
    "Clients fideles",
    "Fort potentiel",
    "Nouveaux clients",
    "A developper",
    "Clients a risque",
]
segment_colors = {
    "Champions": "#1f9d78",
    "Clients fideles": "#2f6fed",
    "Fort potentiel": "#8e5cf7",
    "Nouveaux clients": "#f59e0b",
    "A developper": "#64748b",
    "Clients a risque": "#dc2626",
}

app = dash.Dash(__name__, assets_folder=str(ROOT_DIR / "assets"), eager_loading=True)
app.title = "Dashboard RFM Marketing"

app.layout = html.Div(
    className="page",
    children=[
        html.Div(
            className="header",
            children=[
                html.Div(
                    className="title-block",
                    children=[
                        html.Span("Dashboard marketing", className="eyebrow"),
                        html.H1(["Segmentation client ", html.Span("e-commerce", className="nowrap")]),
                        html.P("Pilotage RFM, valeur client et priorites d'activation commerciale"),
                    ],
                ),
                html.Div(
                    className="filter-card",
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
        html.Div(id="insight-strip", className="insight-strip"),
        html.Div(
            className="kpi-grid",
            children=[
                html.Div([html.Span("Clients"), html.Strong(id="kpi-clients"), html.Small("Base filtree")], className="kpi"),
                html.Div([html.Span("CA total"), html.Strong(id="kpi-revenue"), html.Small("Montant cumule")], className="kpi"),
                html.Div([html.Span("Panier moyen client"), html.Strong(id="kpi-average"), html.Small("Valeur moyenne")], className="kpi"),
                html.Div([html.Span("Recence moyenne"), html.Strong(id="kpi-recency"), html.Small("Jours depuis achat")], className="kpi"),
            ],
        ),
        html.Div(
            className="charts",
            children=[
                dcc.Graph(id="segment-chart", config={"displayModeBar": False}),
                dcc.Graph(id="city-chart", config={"displayModeBar": False}),
                dcc.Graph(id="channel-chart", config={"displayModeBar": False}),
                dcc.Graph(id="rfm-scatter", config={"displayModeBar": False}),
            ],
        ),
        html.Div(
            className="table-panel",
            children=[
                html.Div(
                    className="section-heading",
                    children=[
                        html.H2("Clients prioritaires"),
                        html.P("Classement des clients a contacter en premier selon le score RFM."),
                    ],
                ),
                html.Div(id="priority-table", className="priority-table"),
            ],
        ),
    ],
)


@app.callback(
    Output("kpi-clients", "children"),
    Output("kpi-revenue", "children"),
    Output("kpi-average", "children"),
    Output("kpi-recency", "children"),
    Output("insight-strip", "children"),
    Output("segment-chart", "figure"),
    Output("city-chart", "figure"),
    Output("channel-chart", "figure"),
    Output("rfm-scatter", "figure"),
    Output("priority-table", "children"),
    Input("segment-filter", "value"),
)
def update_dashboard(selected_segment: str):
    filtered = df if selected_segment == "all" else df[df["segment"] == selected_segment]

    clients = filtered["customer_id"].nunique()
    revenue = filtered["monetary_value"].sum()
    average = revenue / clients if clients else 0
    recency = filtered["recency_days"].mean() if clients else 0

    top_segment = (
        filtered.groupby("segment", as_index=False)["customer_id"]
        .nunique()
        .sort_values("customer_id", ascending=False)
        .head(1)
    )
    top_segment_name = top_segment.iloc[0]["segment"] if not top_segment.empty else "Aucun segment"
    action_text = (
        "Comparer les segments pour arbitrer les efforts CRM."
        if selected_segment == "all"
        else segment_actions.get(selected_segment, "Analyser le comportement du segment.")
    )
    insight = [
        html.Strong(f"Segment dominant : {top_segment_name}"),
        html.Span(action_text),
    ]

    segment_fig = px.bar(
        filtered.groupby("segment", as_index=False)
        .agg(customers=("customer_id", "nunique"), revenue=("monetary_value", "sum"))
        .sort_values("customers", ascending=False),
        x="segment",
        y="customers",
        color="segment",
        category_orders={"segment": segment_order},
        color_discrete_map=segment_colors,
        title="Volume client par segment",
        labels={"segment": "", "customers": "Clients"},
    )

    city_fig = px.bar(
        filtered.groupby("city", as_index=False)
        .agg(revenue=("monetary_value", "sum"))
        .sort_values("revenue", ascending=False)
        .head(10),
        x="city",
        y="revenue",
        title="Chiffre d'affaires par ville",
        labels={"city": "", "revenue": "CA"},
        color_discrete_sequence=["#2f6fed"],
    )

    channel_fig = px.pie(
        filtered.groupby("acquisition_channel", as_index=False)
        .agg(revenue=("monetary_value", "sum")),
        names="acquisition_channel",
        values="revenue",
        title="Revenu par canal d'acquisition",
        hole=0.45,
        color_discrete_sequence=["#2f6fed", "#1f9d78", "#f59e0b", "#8e5cf7", "#dc2626"],
    )

    scatter_fig = px.scatter(
        filtered,
        x="frequency_orders",
        y="monetary_value",
        size="recency_days",
        color="segment",
        color_discrete_map=segment_colors,
        hover_data=["customer_id", "city", "rfm_score"],
        title="Lecture RFM : frequence vs valeur",
        labels={
            "frequency_orders": "Commandes",
            "monetary_value": "CA client",
            "segment": "Segment",
            "recency_days": "Recence",
        },
    )

    for figure in (segment_fig, city_fig, channel_fig, scatter_fig):
        figure.update_layout(
            template="plotly_white",
            margin=dict(l=36, r=24, t=58, b=42),
            legend_title_text="",
            font=dict(family="Arial", size=13),
            title_font=dict(size=17),
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",
        )
        figure.update_xaxes(showgrid=False)
        figure.update_yaxes(gridcolor="#edf1f5")

    segment_fig.update_layout(showlegend=False)
    city_fig.update_layout(showlegend=False)
    channel_fig.update_traces(textposition="inside", textinfo="percent+label")
    scatter_fig.update_traces(marker=dict(line=dict(width=0.5, color="#ffffff"), opacity=0.78))

    table_data = (
        filtered.sort_values(["rfm_score", "monetary_value"], ascending=False)
        .head(8)
        .assign(
            monetary_value=lambda data: data["monetary_value"].map(lambda value: f"{value:,.0f} EUR".replace(",", " ")),
            recency_days=lambda data: data["recency_days"].map(lambda value: f"{int(value)} j"),
        )[
            [
                "customer_id",
                "segment",
                "city",
                "rfm_score",
                "monetary_value",
                "frequency_orders",
                "recency_days",
            ]
        ]
        .to_dict("records")
    )
    table = build_priority_table(table_data)

    return (
        f"{clients}",
        f"{revenue:,.0f} EUR".replace(",", " "),
        f"{average:,.0f} EUR".replace(",", " "),
        f"{recency:.0f} j",
        insight,
        segment_fig,
        city_fig,
        channel_fig,
        scatter_fig,
        table,
    )


def build_priority_table(rows: list[dict]) -> html.Table:
    headers = [
        ("customer_id", "Client ID"),
        ("segment", "Segment"),
        ("city", "Ville"),
        ("rfm_score", "Score RFM"),
        ("monetary_value", "CA"),
        ("frequency_orders", "Commandes"),
        ("recency_days", "Recence"),
    ]
    return html.Table(
        [
            html.Thead(html.Tr([html.Th(label) for _, label in headers])),
            html.Tbody(
                [
                    html.Tr([html.Td(row[column]) for column, _ in headers])
                    for row in rows
                ]
            ),
        ]
    )


if __name__ == "__main__":
    app.run_server(debug=False, host="127.0.0.1", port=8050, use_reloader=False, threaded=True)
