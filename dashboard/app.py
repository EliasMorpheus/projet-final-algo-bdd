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

segment_order = [
    "Champions",
    "Clients fideles",
    "Fort potentiel",
    "Nouveaux clients",
    "A developper",
    "Clients a risque",
]
segment_colors = {
    "Champions": "#149a7b",
    "Clients fideles": "#2563eb",
    "Fort potentiel": "#7c3aed",
    "Nouveaux clients": "#d97706",
    "A developper": "#64748b",
    "Clients a risque": "#dc2626",
}
segment_actions = {
    "Champions": "Programme VIP, ventes privees, parrainage et early access.",
    "Clients fideles": "Avantages recurrents, cross-sell et contenu relationnel.",
    "Clients a risque": "Reactivation rapide avec offre limitee et message personnalise.",
    "Nouveaux clients": "Onboarding post-achat et incitation au deuxieme achat.",
    "Fort potentiel": "Bundles premium, recommandations personnalisees et upsell.",
    "A developper": "Nurturing, offres decouverte et tests de messages CRM.",
}


def kpi_card(label: str, value_id: str, caption: str) -> html.Div:
    return html.Div(
        className="kpi-card",
        children=[
            html.Span(label, className="kpi-label"),
            html.Strong(id=value_id),
            html.Small(caption),
        ],
    )


def chart_panel(title: str, subtitle: str, graph_id: str, extra_class: str) -> html.Div:
    return html.Div(
        className=f"panel chart-panel {extra_class}".strip(),
        children=[
            html.Div(
                className="panel-heading",
                children=[html.Div([html.H2(title), html.P(subtitle)])],
            ),
            dcc.Graph(id=graph_id, className="chart", config={"displayModeBar": False}),
        ],
    )


app = dash.Dash(__name__, assets_folder=str(ROOT_DIR / "assets"), eager_loading=True)
app.title = "CRM RFM Command Center"

app.layout = html.Div(
    className="page-shell",
    children=[
        html.Header(
            className="topbar",
            children=[
                html.Div(
                    className="title-stack",
                    children=[
                        html.Span("CRM Performance Monitor", className="eyebrow"),
                        html.H1(["Segmentation client ", html.Span("e-commerce", className="nowrap")]),
                        html.P("Priorisation CRM a partir du scoring RFM, de la valeur client et des canaux d'acquisition."),
                    ],
                ),
                html.Div(
                    className="filter-card",
                    children=[
                        html.Label("Vue segment"),
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
        html.Main(
            className="content",
            children=[
                html.Section(
                    className="kpi-grid",
                    children=[
                        kpi_card("Clients", "kpi-clients", "Base analysee"),
                        kpi_card("CA total", "kpi-revenue", "Valeur transactionnelle"),
                        kpi_card("CA moyen/client", "kpi-average", "Monetary moyen"),
                        kpi_card("Recence moyenne", "kpi-recency", "Dernier achat"),
                    ],
                ),
                html.Section(
                    className="decision-grid",
                    children=[
                        html.Div(
                            className="panel portfolio-panel",
                            children=[
                                html.Div(
                                    className="panel-heading",
                                    children=[
                                        html.Div([html.H2("Portefeuille clients"), html.P("Mix des segments et poids business.")]),
                                        html.Span(id="portfolio-badge", className="status-badge"),
                                    ],
                                ),
                                dcc.Graph(id="segment-chart", className="chart compact-chart", config={"displayModeBar": False}),
                            ],
                        ),
                        html.Div(
                            className="panel action-panel",
                            children=[
                                html.Div(
                                    className="panel-heading",
                                    children=[
                                        html.Div([html.H2("Decision CRM"), html.P("Action recommandee pour la vue active.")]),
                                    ],
                                ),
                                html.Div(id="activation-panel"),
                            ],
                        ),
                    ],
                ),
                html.Section(
                    className="analysis-grid",
                    children=[
                        chart_panel("Lecture RFM", "Frequence d'achat vs valeur client.", "rfm-scatter", "wide"),
                        chart_panel("Revenu par canal", "Contribution des canaux d'acquisition.", "channel-chart", ""),
                        chart_panel("Revenu par ville", "Top villes par chiffre d'affaires.", "city-chart", "wide"),
                    ],
                ),
                html.Section(
                    className="table-panel panel",
                    children=[
                        html.Div(
                            className="panel-heading",
                            children=[
                                html.Div([html.H2("Clients prioritaires"), html.P("Top clients a cibler selon score RFM et valeur.")]),
                                html.Span("Top 8", className="status-badge muted"),
                            ],
                        ),
                        html.Div(id="priority-table", className="priority-table"),
                    ],
                ),
            ],
        ),
    ],
)


@app.callback(
    Output("kpi-clients", "children"),
    Output("kpi-revenue", "children"),
    Output("kpi-average", "children"),
    Output("kpi-recency", "children"),
    Output("portfolio-badge", "children"),
    Output("activation-panel", "children"),
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
    total_revenue = df["monetary_value"].sum()
    revenue_share = revenue / total_revenue if total_revenue else 0

    segment_stats = build_segment_stats(filtered)
    top_segment_name = segment_stats.iloc[0]["segment"] if not segment_stats.empty else "Aucun segment"
    active_label = "Tous segments" if selected_segment == "all" else selected_segment
    action = (
        "Comparer les poches de valeur, puis concentrer les campagnes sur Champions, Fort potentiel et Clients a risque."
        if selected_segment == "all"
        else segment_actions.get(selected_segment, "Analyser le comportement du segment.")
    )

    activation_panel = html.Div(
        className="activation-content",
        children=[
            html.Div(
                className="activation-headline",
                children=[
                    html.Span(active_label),
                    html.Strong(action),
                ],
            ),
            html.Div(
                className="mini-metrics",
                children=[
                    metric_item("Part CA", f"{revenue_share:.0%}"),
                    metric_item("Segment dominant", top_segment_name),
                    metric_item("Clients filtres", str(clients)),
                ],
            ),
            html.Div(
                className="segment-list",
                children=[
                    segment_row(row.segment, int(row.customers), float(row.revenue), total_revenue)
                    for row in segment_stats.itertuples(index=False)
                ],
            ),
        ],
    )

    segment_fig = px.bar(
        segment_stats.sort_values("customers"),
        x="customers",
        y="segment",
        orientation="h",
        color="segment",
        category_orders={"segment": segment_order},
        color_discrete_map=segment_colors,
        text="customers",
        labels={"customers": "Clients", "segment": ""},
    )

    city_fig = px.bar(
        filtered.groupby("city", as_index=False)
        .agg(revenue=("monetary_value", "sum"))
        .sort_values("revenue", ascending=False)
        .head(8),
        x="revenue",
        y="city",
        orientation="h",
        text="revenue",
        labels={"city": "", "revenue": "CA"},
        color_discrete_sequence=["#2563eb"],
    )

    channel_fig = px.pie(
        filtered.groupby("acquisition_channel", as_index=False)
        .agg(revenue=("monetary_value", "sum")),
        names="acquisition_channel",
        values="revenue",
        hole=0.62,
        color_discrete_sequence=["#2563eb", "#149a7b", "#d97706", "#7c3aed", "#dc2626"],
    )

    scatter_fig = px.scatter(
        filtered,
        x="frequency_orders",
        y="monetary_value",
        size="recency_days",
        color="segment",
        color_discrete_map=segment_colors,
        hover_data=["customer_id", "city", "rfm_score"],
        labels={
            "frequency_orders": "Commandes",
            "monetary_value": "CA client",
            "segment": "Segment",
            "recency_days": "Recence",
        },
    )

    style_figures(segment_fig, city_fig, channel_fig, scatter_fig)
    segment_fig.update_layout(showlegend=False, height=560)
    city_fig.update_layout(showlegend=False, height=350)
    city_fig.update_traces(texttemplate="%{text:.0f} EUR", textposition="outside", cliponaxis=False)
    segment_fig.update_traces(textposition="outside", cliponaxis=False)
    channel_fig.update_traces(textposition="inside", textinfo="percent+label")
    scatter_fig.update_layout(height=360)
    scatter_fig.update_traces(marker=dict(line=dict(width=0.7, color="#ffffff"), opacity=0.82))

    table = build_priority_table(filtered)

    return (
        f"{clients}",
        format_eur(revenue),
        format_eur(average),
        f"{recency:.0f} j",
        f"{top_segment_name}",
        activation_panel,
        segment_fig,
        city_fig,
        channel_fig,
        scatter_fig,
        table,
    )


def build_segment_stats(data: pd.DataFrame) -> pd.DataFrame:
    return (
        data.groupby("segment", as_index=False)
        .agg(customers=("customer_id", "nunique"), revenue=("monetary_value", "sum"))
        .assign(order=lambda values: values["segment"].map({name: index for index, name in enumerate(segment_order)}))
        .sort_values(["customers", "revenue"], ascending=False)
    )


def style_figures(*figures) -> None:
    for figure in figures:
        figure.update_layout(
            template="plotly_white",
            margin=dict(l=20, r=28, t=8, b=30),
            legend_title_text="",
            font=dict(family="Arial", size=12, color="#1f2937"),
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",
        )
        figure.update_xaxes(showgrid=True, gridcolor="#edf1f5", zeroline=False)
        figure.update_yaxes(showgrid=False, zeroline=False)


def metric_item(label: str, value: str) -> html.Div:
    return html.Div([html.Span(label), html.Strong(value)], className="metric-item")


def segment_row(segment: str, customers: int, revenue: float, total_revenue: float) -> html.Div:
    share = revenue / total_revenue if total_revenue else 0
    return html.Div(
        className="segment-row",
        children=[
            html.Span(className="segment-dot", style={"backgroundColor": segment_colors.get(segment, "#64748b")}),
            html.Div([html.Strong(segment), html.Small(f"{customers} clients")]),
            html.Span(f"{share:.0%} CA", className="segment-share"),
        ],
    )


def build_priority_table(data: pd.DataFrame) -> html.Table:
    rows = (
        data.sort_values(["rfm_score", "monetary_value"], ascending=False)
        .head(8)
        .assign(
            monetary_value=lambda values: values["monetary_value"].map(format_eur),
            recency_days=lambda values: values["recency_days"].map(lambda value: f"{int(value)} j"),
        )[["customer_id", "segment", "city", "rfm_score", "monetary_value", "frequency_orders", "recency_days"]]
        .to_dict("records")
    )
    headers = [
        ("customer_id", "ID"),
        ("segment", "Segment"),
        ("city", "Ville"),
        ("rfm_score", "RFM"),
        ("monetary_value", "CA"),
        ("frequency_orders", "Cmd"),
        ("recency_days", "Recence"),
    ]
    return html.Table(
        [
            html.Thead(html.Tr([html.Th(label) for _, label in headers])),
            html.Tbody([html.Tr([html.Td(row[column]) for column, _ in headers]) for row in rows]),
        ]
    )


def format_eur(value: float) -> str:
    return f"{value:,.0f} EUR".replace(",", " ")


if __name__ == "__main__":
    app.run_server(debug=False, host="127.0.0.1", port=8050, use_reloader=False, threaded=True)
