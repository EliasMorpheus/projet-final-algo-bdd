from __future__ import annotations

from datetime import datetime
from typing import Dict, Iterable, Optional

import mysql.connector
import pandas as pd
import requests

from config import load_db_config


API_SOURCE = "api-adresse.data.gouv.fr"


def get_connection(database_required: bool = True):
    return mysql.connector.connect(**load_db_config(database_required=database_required))


def fetch_dataframe(query: str) -> pd.DataFrame:
    with get_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query)
        return pd.DataFrame(cursor.fetchall())


def geocode_city(city: str) -> Dict[str, Optional[float]]:
    url = "https://api-adresse.data.gouv.fr/search/"
    params = {"q": city, "type": "municipality", "limit": 1}
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    features = response.json().get("features", [])

    if not features:
        return {"city": city, "latitude": None, "longitude": None}

    longitude, latitude = features[0]["geometry"]["coordinates"]
    return {"city": city, "latitude": latitude, "longitude": longitude}


def enrich_cities(cities: Iterable[str]) -> pd.DataFrame:
    rows = []
    for city in sorted(set(cities)):
        try:
            rows.append(geocode_city(city))
        except requests.RequestException:
            rows.append({"city": city, "latitude": None, "longitude": None})

    enriched = pd.DataFrame(rows)
    enriched["api_source"] = API_SOURCE
    return enriched


def calculate_rfm(transactions: pd.DataFrame) -> pd.DataFrame:
    analysis_date = transactions["order_date"].max() + pd.Timedelta(days=1)

    rfm = (
        transactions.groupby(["customer_id", "city"], as_index=False)
        .agg(
            recency_days=("order_date", lambda values: (analysis_date - values.max()).days),
            frequency_orders=("order_id", "nunique"),
            monetary_value=("order_total", "sum"),
        )
    )

    rfm["r_score"] = pd.qcut(
        rfm["recency_days"].rank(method="first", ascending=False), 5, labels=[1, 2, 3, 4, 5]
    ).astype(int)
    rfm["f_score"] = pd.qcut(
        rfm["frequency_orders"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]
    ).astype(int)
    rfm["m_score"] = pd.qcut(
        rfm["monetary_value"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]
    ).astype(int)
    rfm["rfm_score"] = rfm["r_score"] * 100 + rfm["f_score"] * 10 + rfm["m_score"]
    rfm["segment"] = rfm.apply(assign_segment, axis=1)

    return rfm


def assign_segment(row: pd.Series) -> str:
    if row["r_score"] >= 4 and row["f_score"] >= 4 and row["m_score"] >= 4:
        return "Champions"
    if row["r_score"] >= 4 and row["f_score"] >= 3:
        return "Clients fideles"
    if row["r_score"] <= 2 and row["m_score"] >= 4:
        return "Clients a risque"
    if row["r_score"] >= 4 and row["frequency_orders"] <= 2:
        return "Nouveaux clients"
    if row["m_score"] >= 4:
        return "Fort potentiel"
    return "A developper"


def replace_city_enrichment(enriched: pd.DataFrame) -> None:
    sql = """
        REPLACE INTO city_enrichment (city, latitude, longitude, api_source)
        VALUES (%s, %s, %s, %s)
    """
    values = [
        (
            row.city,
            None if pd.isna(row.latitude) else float(row.latitude),
            None if pd.isna(row.longitude) else float(row.longitude),
            row.api_source,
        )
        for row in enriched.itertuples(index=False)
    ]

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.executemany(sql, values)
        connection.commit()


def replace_rfm_scores(rfm: pd.DataFrame) -> None:
    sql = """
        REPLACE INTO rfm_scores (
            customer_id, recency_days, frequency_orders, monetary_value,
            r_score, f_score, m_score, rfm_score, segment,
            city, latitude, longitude, calculated_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    calculated_at = datetime.now()
    values = [
        (
            int(row.customer_id),
            int(row.recency_days),
            int(row.frequency_orders),
            float(row.monetary_value),
            int(row.r_score),
            int(row.f_score),
            int(row.m_score),
            int(row.rfm_score),
            row.segment,
            row.city,
            None if pd.isna(row.latitude) else float(row.latitude),
            None if pd.isna(row.longitude) else float(row.longitude),
            calculated_at,
        )
        for row in rfm.itertuples(index=False)
    ]

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM rfm_scores")
        cursor.executemany(sql, values)
        connection.commit()


def main() -> None:
    query = """
        SELECT
            c.customer_id,
            c.city,
            o.order_id,
            o.order_date,
            SUM(oi.quantity * oi.unit_price) AS order_total
        FROM customers c
        JOIN orders o ON o.customer_id = c.customer_id
        JOIN order_items oi ON oi.order_id = o.order_id
        WHERE o.order_status = 'paid'
        GROUP BY c.customer_id, c.city, o.order_id, o.order_date
    """

    transactions = fetch_dataframe(query)
    transactions["order_date"] = pd.to_datetime(transactions["order_date"])

    enriched = enrich_cities(transactions["city"])
    replace_city_enrichment(enriched)

    rfm = calculate_rfm(transactions)
    rfm = rfm.merge(enriched, on="city", how="left")
    replace_rfm_scores(rfm)

    print(f"Pipeline termine: {len(rfm)} clients scores et {len(enriched)} villes enrichies.")


if __name__ == "__main__":
    main()
