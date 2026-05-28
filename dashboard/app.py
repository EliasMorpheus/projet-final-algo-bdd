from __future__ import annotations

import math
from pathlib import Path
import sys

import dash
from dash import Input, Output, State, ctx, dcc, html
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
segments = ["Champions", "Clients fideles", "Fort potentiel", "Nouveaux clients", "A developper", "Clients a risque"]
channels = sorted(df["acquisition_channel"].unique())
cities = sorted(df["city"].unique())
rfm_min, rfm_max = int(df["rfm_score"].min()), int(df["rfm_score"].max())
revenue_min = math.floor(float(df["monetary_value"].min()))
revenue_max = math.ceil(float(df["monetary_value"].max()))

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
        children=[html.Span(label, className="kpi-label"), html.Strong(id=value_id), html.Small(caption)],
    )


def filter_group(label: str, control) -> html.Div:
    return html.Div([html.Label(label), control], className="filter-group")


def panel(title: str, subtitle: str, child, extra_class: str = "") -> html.Div:
    return html.Div(
        className=f"panel {extra_class}".strip(),
        children=[
            html.Div(className="panel-heading", children=[html.Div([html.H2(title), html.P(subtitle)])]),
            child,
        ],
    )


app = dash.Dash(__name__, assets_folder=str(ROOT_DIR / "assets"), eager_loading=True)
app.title = "CRM RFM Command Center"

app.layout = html.Div(
    className="page-shell",
    children=[
        dcc.Store(id="cross-filter-store", data={"segment": None, "channel": None, "city": None}),
        html.Header(
            className="topbar",
            children=[
                html.Div(
                    className="title-stack",
                    children=[
                        html.Span("CRM Performance Monitor", className="eyebrow"),
                        html.H1(["Segmentation client ", html.Span("e-commerce", className="nowrap")]),
                        html.P("Dashboard interactif RFM pour arbitrer les actions CRM par valeur, risque et canal."),
                    ],
                ),
                html.Div(id="active-filter-strip", className="active-filter-strip"),
            ],
        ),
        html.Main(
            className="dashboard-layout",
            children=[
                html.Aside(
                    className="filter-sidebar",
                    children=[
                        html.Div(
                            className="filter-header",
                            children=[
                                html.H2("Filtres"),
                                html.Button("Effacer les clics", id="clear-cross-filter", n_clicks=0, className="ghost-button"),
                            ],
                        ),
                        filter_group(
                            "Segments",
                            dcc.Dropdown(
                                id="segment-filter",
                                options=[{"label": value, "value": value} for value in segments],
                                value=[],
                                multi=True,
                                placeholder="Tous",
                            ),
                        ),
                        filter_group(
                            "Canaux d'acquisition",
                            dcc.Dropdown(
                                id="channel-filter",
                                options=[{"label": value, "value": value} for value in channels],
                                value=[],
                                multi=True,
                                placeholder="Tous",
                            ),
                        ),
                        filter_group(
                            "Villes",
                            dcc.Dropdown(
                                id="city-filter",
                                options=[{"label": value, "value": value} for value in cities],
                                value=[],
                                multi=True,
                                placeholder="Toutes",
                            ),
                        ),
                        filter_group(
                            "Score RFM",
                            dcc.RangeSlider(
                                id="rfm-filter",
                                min=rfm_min,
                                max=rfm_max,
                                step=1,
                                value=[rfm_min, rfm_max],
                                marks={rfm_min: str(rfm_min), rfm_max: str(rfm_max)},
                                tooltip={"placement": "bottom", "always_visible": False},
                            ),
                        ),
                        filter_group(
                            "CA client",
                            dcc.RangeSlider(
                                id="revenue-filter",
                                min=revenue_min,
                                max=revenue_max,
                                step=50,
                                value=[revenue_min, revenue_max],
                                marks={
                                    revenue_min: f"{revenue_min} EUR",
                                    revenue_max: f"{revenue_max} EUR",
                                },
                                tooltip={"placement": "bottom", "always_visible": False},
                            ),
                        ),
                    ],
                ),
                html.Section(
                    className="main-board",
                    children=[
                        html.Section(
                            className="kpi-grid",
                            children=[
                                kpi_card("Clients", "kpi-clients", "Base filtree"),
                                kpi_card("CA total", "kpi-revenue", "Valeur transactionnelle"),
                                kpi_card("CA moyen/client", "kpi-average", "Monetary moyen"),
                                kpi_card("Recence moyenne", "kpi-recency", "Dernier achat"),
                            ],
                        ),
                        html.Section(
                            className="balanced-grid top-analysis",
                            children=[
                                panel(
                                    "Portefeuille clients",
                                    "Clique sur un segment pour croiser le filtre.",
                                    dcc.Graph(id="segment-chart", className="chart", config={"displayModeBar": False}),
                                ),
                                panel(
                                    "Decision CRM",
                                    "Synthese de la vue active.",
                                    html.Div(id="activation-panel"),
                                    "decision-panel",
                                ),
                            ],
                        ),
                        html.Section(
                            className="balanced-grid analysis-grid",
                            children=[
                                panel(
                                    "Lecture RFM",
                                    "Frequence d'achat vs valeur client.",
                                    dcc.Graph(id="rfm-scatter", className="chart", config={"displayModeBar": False}),
                                ),
                                panel(
                                    "Canaux",
                                    "Clique sur un canal pour filtrer.",
                                    dcc.Graph(id="channel-chart", className="chart", config={"displayModeBar": False}),
                                ),
                                panel(
                                    "Villes",
                                    "Clique sur une ville pour filtrer.",
                                    dcc.Graph(id="city-chart", className="chart", config={"displayModeBar": False}),
                                ),
                                panel(
                                    "Clients prioritaires",
                                    "Top clients selon RFM et valeur.",
                                    html.Div(id="priority-table", className="priority-table"),
                                    "table-panel",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    ],
)


@app.callback(
    Output("cross-filter-store", "data"),
    Input("segment-chart", "clickData"),
    Input("channel-chart", "clickData"),
    Input("city-chart", "clickData"),
    Input("clear-cross-filter", "n_clicks"),
    State("cross-filter-store", "data"),
)
def update_cross_filter(segment_click, channel_click, city_click, clear_clicks, current):
    current = current or {"segment": None, "channel": None, "city": None}
    trigger = ctx.triggered_id

    if trigger == "clear-cross-filter":
        return {"segment": None, "channel": None, "city": None}
    if trigger == "segment-chart" and segment_click:
        selected = segment_click["points"][0].get("y")
        return toggle_value(current, "segment", selected)
    if trigger == "channel-chart" and channel_click:
        selected = channel_click["points"][0].get("label")
        return toggle_value(current, "channel", selected)
    if trigger == "city-chart" and city_click:
        selected = city_click["points"][0].get("y")
        return toggle_value(current, "city", selected)
    return current


@app.callback(
    Output("kpi-clients", "children"),
    Output("kpi-revenue", "children"),
    Output("kpi-average", "children"),
    Output("kpi-recency", "children"),
    Output("active-filter-strip", "children"),
    Output("activation-panel", "children"),
    Output("segment-chart", "figure"),
    Output("city-chart", "figure"),
    Output("channel-chart", "figure"),
    Output("rfm-scatter", "figure"),
    Output("priority-table", "children"),
    Input("segment-filter", "value"),
    Input("channel-filter", "value"),
    Input("city-filter", "value"),
    Input("rfm-filter", "value"),
    Input("revenue-filter", "value"),
    Input("cross-filter-store", "data"),
)
def update_dashboard(selected_segments, selected_channels, selected_cities, rfm_range, revenue_range, cross_filter):
    filtered = apply_filters(
        df,
        selected_segments or [],
        selected_channels or [],
        selected_cities or [],
        rfm_range,
        revenue_range,
        cross_filter or {},
    )

    clients = filtered["customer_id"].nunique()
    revenue = filtered["monetary_value"].sum()
    average = revenue / clients if clients else 0
    recency = filtered["recency_days"].mean() if clients else 0
    total_revenue = df["monetary_value"].sum()
    revenue_share = revenue / total_revenue if total_revenue else 0

    segment_stats = build_segment_stats(filtered)
    revenue_ranked_segments = segment_stats.sort_values(["revenue", "customers"], ascending=False)
    top_segment = revenue_ranked_segments.iloc[0]["segment"] if not revenue_ranked_segments.empty else "Aucun segment"
    action = segment_actions.get(top_segment, "Comparer les segments pour arbitrer les efforts CRM.")

    activation_panel = build_activation_panel(top_segment, action, revenue_share, clients, cross_filter or {})

    segment_fig = build_segment_figure(segment_stats, (cross_filter or {}).get("segment"))
    channel_fig = build_channel_figure(filtered, (cross_filter or {}).get("channel"))
    city_fig = build_city_figure(filtered, (cross_filter or {}).get("city"))
    scatter_fig = build_scatter_figure(filtered)

    return (
        str(clients),
        format_eur(revenue),
        format_eur(average),
        f"{recency:.0f} j",
        build_filter_chips(selected_segments or [], selected_channels or [], selected_cities or [], rfm_range, revenue_range, cross_filter or {}),
        activation_panel,
        segment_fig,
        city_fig,
        channel_fig,
        scatter_fig,
        build_priority_table(filtered),
    )


def toggle_value(current: dict, key: str, value: str | None) -> dict:
    updated = {**current}
    updated[key] = None if current.get(key) == value else value
    return updated


def apply_filters(data, selected_segments, selected_channels, selected_cities, rfm_range, revenue_range, cross_filter):
    filtered = data.copy()
    if selected_segments:
        filtered = filtered[filtered["segment"].isin(selected_segments)]
    if selected_channels:
        filtered = filtered[filtered["acquisition_channel"].isin(selected_channels)]
    if selected_cities:
        filtered = filtered[filtered["city"].isin(selected_cities)]
    if rfm_range:
        filtered = filtered[filtered["rfm_score"].between(rfm_range[0], rfm_range[1])]
    if revenue_range:
        filtered = filtered[filtered["monetary_value"].between(revenue_range[0], revenue_range[1])]
    if cross_filter.get("segment"):
        filtered = filtered[filtered["segment"] == cross_filter["segment"]]
    if cross_filter.get("channel"):
        filtered = filtered[filtered["acquisition_channel"] == cross_filter["channel"]]
    if cross_filter.get("city"):
        filtered = filtered[filtered["city"] == cross_filter["city"]]
    return filtered


def build_filter_chips(segments_selected, channels_selected, cities_selected, rfm_range, revenue_range, cross_filter):
    chips = []
    for value in segments_selected:
        chips.append(chip(f"Segment: {value}"))
    for value in channels_selected:
        chips.append(chip(f"Canal: {value}"))
    for value in cities_selected:
        chips.append(chip(f"Ville: {value}"))
    if rfm_range and (rfm_range[0] != rfm_min or rfm_range[1] != rfm_max):
        chips.append(chip(f"RFM {rfm_range[0]}-{rfm_range[1]}"))
    if revenue_range and (revenue_range[0] != revenue_min or revenue_range[1] != revenue_max):
        chips.append(chip(f"CA {revenue_range[0]}-{revenue_range[1]} EUR"))
    for key, label in [("segment", "Clic segment"), ("channel", "Clic canal"), ("city", "Clic ville")]:
        if cross_filter.get(key):
            chips.append(chip(f"{label}: {cross_filter[key]}", "cross"))
    return chips or [html.Span("Aucun filtre actif", className="chip muted")]


def chip(text: str, extra_class: str = ""):
    return html.Span(text, className=f"chip {extra_class}".strip())


def build_activation_panel(top_segment: str, action: str, revenue_share: float, clients: int, cross_filter: dict):
    clicked = [value for value in cross_filter.values() if value]
    return html.Div(
        className="activation-content",
        children=[
            html.Div(
                className="activation-headline",
                children=[
                    html.Span(top_segment),
                    html.Strong(action),
                ],
            ),
            html.Div(
                className="mini-metrics",
                children=[
                    metric_item("Part CA", f"{revenue_share:.0%}"),
                    metric_item("Clients filtres", str(clients)),
                    metric_item("Clic actif", " / ".join(clicked) if clicked else "Aucun"),
                ],
            ),
        ],
    )


def build_segment_stats(data: pd.DataFrame) -> pd.DataFrame:
    if data.empty:
        return pd.DataFrame({"segment": segments, "customers": [0] * len(segments), "revenue": [0] * len(segments)})
    stats = (
        data.groupby("segment", as_index=False)
        .agg(customers=("customer_id", "nunique"), revenue=("monetary_value", "sum"))
        .set_index("segment")
        .reindex(segments, fill_value=0)
        .reset_index()
    )
    return stats


def build_segment_figure(stats: pd.DataFrame, selected_segment: str | None):
    figure = px.bar(
        stats,
        x="customers",
        y="segment",
        orientation="h",
        color="segment",
        category_orders={"segment": segments},
        color_discrete_map=segment_colors,
        text="customers",
        labels={"customers": "Clients", "segment": ""},
    )
    style_figure(figure)
    figure.update_layout(showlegend=False, height=310, clickmode="event+select")
    figure.update_traces(textposition="outside", cliponaxis=False, marker_line_width=0)
    dim_unselected(figure, selected_segment)
    return figure


def build_channel_figure(data: pd.DataFrame, selected_channel: str | None):
    stats = data.groupby("acquisition_channel", as_index=False).agg(revenue=("monetary_value", "sum"))
    figure = px.pie(
        stats,
        names="acquisition_channel",
        values="revenue",
        hole=0.58,
        color_discrete_sequence=["#2563eb", "#149a7b", "#d97706", "#7c3aed", "#dc2626"],
    )
    style_figure(figure)
    figure.update_layout(height=300, clickmode="event+select")
    figure.update_traces(textposition="inside", textinfo="percent+label", pull=[0.05 if label == selected_channel else 0 for label in stats["acquisition_channel"]])
    return figure


def build_city_figure(data: pd.DataFrame, selected_city: str | None):
    stats = (
        data.groupby("city", as_index=False)
        .agg(revenue=("monetary_value", "sum"))
        .sort_values("revenue", ascending=True)
        .tail(8)
    )
    figure = px.bar(
        stats,
        x="revenue",
        y="city",
        orientation="h",
        text="revenue",
        labels={"city": "", "revenue": "CA"},
        color_discrete_sequence=["#2563eb"],
    )
    style_figure(figure)
    figure.update_layout(showlegend=False, height=300, clickmode="event+select")
    figure.update_traces(texttemplate="%{text:.0f} EUR", textposition="outside", cliponaxis=False)
    if selected_city:
        opacities = [1 if city == selected_city else 0.3 for city in stats["city"]]
        figure.update_traces(marker_opacity=opacities)
    return figure


def build_scatter_figure(data: pd.DataFrame):
    figure = px.scatter(
        data,
        x="frequency_orders",
        y="monetary_value",
        size="recency_days",
        color="segment",
        color_discrete_map=segment_colors,
        hover_data=["customer_id", "city", "acquisition_channel", "rfm_score"],
        labels={"frequency_orders": "Commandes", "monetary_value": "CA client", "segment": "Segment"},
    )
    style_figure(figure)
    figure.update_layout(height=300, legend=dict(orientation="h", y=-0.22, x=0))
    figure.update_traces(marker=dict(line=dict(width=0.7, color="#ffffff"), opacity=0.82))
    return figure


def style_figure(figure) -> None:
    figure.update_layout(
        template="plotly_white",
        margin=dict(l=18, r=24, t=8, b=32),
        legend_title_text="",
        font=dict(family="Arial", size=12, color="#1f2937"),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
    )
    figure.update_xaxes(showgrid=True, gridcolor="#edf1f5", zeroline=False)
    figure.update_yaxes(showgrid=False, zeroline=False)


def dim_unselected(figure, selected_segment: str | None) -> None:
    if not selected_segment:
        return
    for trace in figure.data:
        trace.opacity = 1 if trace.name == selected_segment else 0.25


def metric_item(label: str, value: str) -> html.Div:
    return html.Div([html.Span(label), html.Strong(value)], className="metric-item")


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
