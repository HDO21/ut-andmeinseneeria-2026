from __future__ import annotations

import os

import pandas as pd
import psycopg2
import streamlit as st


st.set_page_config(
    page_title="Ilmaandmete näidikulaud",
    page_icon=None,
    layout="wide",
)


def get_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "db"),
        port=os.environ.get("DB_PORT", "5432"),
        user=os.environ.get("DB_USER", "praktikum"),
        password=os.environ.get("DB_PASSWORD", "praktikum"),
        dbname=os.environ.get("DB_NAME", "praktikum"),
    )


@st.cache_data(ttl=60)
def load_dataframe(query: str) -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query(query, conn)


st.title("Tartu ja Tallinna ilmaotsuse näidik")

daily = load_dataframe(
    """
    SELECT
        location_name,
        forecast_date,
        forecast_hours,
        avg_temp_c,
        max_temp_c,
        total_precipitation_mm,
        max_wind_speed_ms,
        hours_with_precipitation,
        weather_risk_level
    FROM mart.latest_daily_weather_summary
    ORDER BY forecast_date, location_name
    """
)

latest_run = load_dataframe(
    """
    SELECT
        run_id::text AS run_id,
        fetched_at,
        forecast_days,
        status,
        message
    FROM mart.latest_pipeline_run
    """
)

quality = load_dataframe(
    """
    SELECT
        test_name,
        status,
        failed_rows,
        message
    FROM quality.test_results
    ORDER BY test_name
    """
)

if daily.empty:
    st.warning("Andmeid ei ole veel laaditud. Käivita terminalis `docker compose exec pipeline python scripts/run_pipeline.py run-all`.")
    st.stop()

locations = sorted(daily["location_name"].unique())
selected_locations = st.sidebar.multiselect(
    "Asukohad",
    options=locations,
    default=locations,
)

filtered = daily[daily["location_name"].isin(selected_locations)].copy()

if latest_run.empty:
    st.info("Viimase laadimise infot ei leitud.")
else:
    run = latest_run.iloc[0]
    st.caption(f"Viimane laadimine: {run['fetched_at']} | {run['message']}")

metric_1, metric_2, metric_3, metric_4 = st.columns(4)
metric_1.metric("Keskmine temperatuur", f"{filtered['avg_temp_c'].mean():.1f} °C")
metric_2.metric("Sademed kokku", f"{filtered['total_precipitation_mm'].sum():.1f} mm")
metric_3.metric("Suurim tuulekiirus", f"{filtered['max_wind_speed_ms'].max():.1f} m/s")
metric_4.metric("Sademetega tunde", int(filtered["hours_with_precipitation"].sum()))

temperature = filtered.pivot(
    index="forecast_date",
    columns="location_name",
    values="avg_temp_c",
)

precipitation = filtered.pivot(
    index="forecast_date",
    columns="location_name",
    values="total_precipitation_mm",
)

st.subheader("Keskmine temperatuur")
st.line_chart(temperature)

st.subheader("Sademed päevas")
st.bar_chart(precipitation)

st.subheader("Päevane kokkuvõte")
st.dataframe(
    filtered[
        [
            "location_name",
            "forecast_date",
            "forecast_hours",
            "avg_temp_c",
            "max_temp_c",
            "total_precipitation_mm",
            "max_wind_speed_ms",
            "hours_with_precipitation",
            "weather_risk_level",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

st.subheader("Andmekvaliteedi kontrollid")
st.dataframe(quality, use_container_width=True, hide_index=True)
