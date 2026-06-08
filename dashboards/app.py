from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


DATA_PATH = Path("data/processed/weather_unified.parquet")
PREDICTIONS_PATH = Path("data/processed/weather_predictions.parquet")
METRICS_PATH = Path("models/temp_max_next_day_model.metrics.json")


st.set_page_config(
    page_title="ClimaCentral AI",
    page_icon="🌦️",
    layout="wide",
)


@st.cache_data
def load_weather_data() -> pd.DataFrame:
    """Carga el dataframe analítico único generado por el ETL."""
    if DATA_PATH.exists():
        df = pd.read_parquet(DATA_PATH)
    elif DATA_PATH.with_suffix(".csv").exists():
        df = pd.read_csv(DATA_PATH.with_suffix(".csv"))
    else:
        return pd.DataFrame()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # La columna source se conserva solo para trazabilidad técnica.
    # El usuario final trabaja con una única fuente analítica unificada.
    if "is_forecast" not in df.columns:
        df["is_forecast"] = df.get("source", "").eq("open_meteo_api")

    return df


@st.cache_data
def load_predictions() -> pd.DataFrame:
    """Carga predicciones generadas a partir del dataframe unificado."""
    if PREDICTIONS_PATH.exists():
        df = pd.read_parquet(PREDICTIONS_PATH)
    elif PREDICTIONS_PATH.with_suffix(".csv").exists():
        df = pd.read_csv(PREDICTIONS_PATH.with_suffix(".csv"))
    else:
        return pd.DataFrame()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def risk_label(value: float) -> str:
    if pd.isna(value):
        return "Sin dato"
    if value >= 10:
        return "Alto"
    if value >= 2:
        return "Medio"
    return "Bajo"


weather_df = load_weather_data()
pred_df = load_predictions()

st.title("🌦️ ClimaCentral AI")
st.caption(
    "Producto de monitoreo y predicción climática para la zona central de Chile. "
    "El dashboard consume una única fuente analítica: data/processed/weather_unified.parquet."
)

if weather_df.empty:
    st.error(
        "No se encontró data/processed/weather_unified.parquet. "
        "Ejecuta primero el pipeline ETL."
    )
    st.stop()

cities = sorted(weather_df["city"].dropna().unique().tolist())

with st.sidebar:
    st.header("Parámetros del producto")
    selected_city = st.selectbox("Ciudad", cities)

    min_date = weather_df["date"].min().date()
    max_date = weather_df["date"].max().date()

    selected_range = st.date_input(
        "Rango de análisis",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    variable = st.selectbox(
        "Indicador climático",
        [
            "temp_max",
            "temp_mean",
            "temp_min",
            "precipitation_sum",
            "wind_speed_max",
        ],
    )

filtered = weather_df[weather_df["city"].eq(selected_city)].copy()

if isinstance(selected_range, tuple) and len(selected_range) == 2:
    start_date, end_date = selected_range
    filtered = filtered[
        (filtered["date"].dt.date >= start_date)
        & (filtered["date"].dt.date <= end_date)
    ]

filtered = filtered.sort_values("date")

historical_filtered = filtered[~filtered["is_forecast"].astype(bool)].copy()
forecast_filtered = filtered[filtered["is_forecast"].astype(bool)].copy()

last_historical = historical_filtered.sort_values("date").tail(1)
last_available = filtered.sort_values("date").tail(1)

col1, col2, col3, col4 = st.columns(4)

if not last_available.empty:
    metric_row = last_historical if not last_historical.empty else last_available

    col1.metric("Temp. máxima reciente", f"{metric_row['temp_max'].iloc[0]:.1f} °C")
    col2.metric("Temp. mínima reciente", f"{metric_row['temp_min'].iloc[0]:.1f} °C")
    col3.metric("Precipitación reciente", f"{metric_row['precipitation_sum'].iloc[0]:.1f} mm")
    col4.metric("Riesgo lluvia", risk_label(metric_row["precipitation_sum"].iloc[0]))

st.subheader("Serie climática unificada")

st.write(
    "El usuario no selecciona una fuente de datos. El ETL normaliza el histórico y la API "
    "en un único dataframe analítico; la columna de origen queda solo como trazabilidad técnica."
)

fig = px.line(
    filtered,
    x="date",
    y=variable,
    markers=True,
    title=f"{variable} unificado - {selected_city}",
)

if not forecast_filtered.empty:
    first_forecast_date = forecast_filtered["date"].min()
    fig.add_vline(
        x=first_forecast_date,
        line_dash="dash",
        annotation_text="inicio pronóstico",
        annotation_position="top left",
    )

fig.update_layout(
    xaxis_title="Fecha",
    yaxis_title=variable,
    legend_title_text="",
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("Predicción generada por ClimaCentral AI")

city_pred = pd.DataFrame()
if not pred_df.empty:
    city_pred = pred_df[pred_df["city"].eq(selected_city)].sort_values("date")

if city_pred.empty:
    st.warning(
        "Todavía no hay predicciones generadas. "
        "Ejecuta: python -m ml.predict"
    )
else:
    next_prediction = city_pred.head(1)

    c1, c2, c3 = st.columns(3)
    c1.metric(
        "Temp. máxima estimada día siguiente",
        f"{next_prediction['pred_temp_max_next_day'].iloc[0]:.1f} °C",
    )
    c2.metric(
        "Temp. máxima base del pronóstico",
        f"{next_prediction['temp_max'].iloc[0]:.1f} °C",
    )
    c3.metric(
        "Riesgo lluvia",
        str(next_prediction["rain_risk"].iloc[0]).upper(),
    )

    pred_plot_df = city_pred[
        ["date", "temp_max", "pred_temp_max_next_day"]
    ].rename(
        columns={
            "temp_max": "temperatura_base",
            "pred_temp_max_next_day": "prediccion_ml_dia_siguiente",
        }
    )

    pred_fig = px.line(
        pred_plot_df,
        x="date",
        y=["temperatura_base", "prediccion_ml_dia_siguiente"],
        markers=True,
        title=f"Predicción operativa - {selected_city}",
    )
    pred_fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Temperatura máxima °C",
        legend_title_text="Indicador",
    )
    st.plotly_chart(pred_fig, use_container_width=True)

    st.dataframe(
        city_pred[
            [
                "date",
                "city",
                "temp_min",
                "temp_max",
                "pred_temp_max_next_day",
                "precipitation_sum",
                "rain_risk",
            ]
        ],
        use_container_width=True,
    )

st.subheader("Valor del producto")

st.info(
    "ClimaCentral AI transforma fuentes heterogéneas en una sola base analítica, "
    "permite monitorear variables climáticas relevantes y entrega predicciones para "
    "apoyar planificación operativa en agricultura, logística, transporte, eventos y gestión municipal."
)

with st.expander("Trazabilidad técnica de datos"):
    st.write(
        "Esta sección es para defensa técnica. La columna source permite auditar de dónde vino cada registro, "
        "pero no se expone como decisión principal para el usuario final."
    )

    if "source" in weather_df.columns:
        source_summary = (
            weather_df.groupby(["source", "city"])
            .size()
            .reset_index(name="filas")
            .sort_values(["source", "city"])
        )
        st.dataframe(source_summary, use_container_width=True)

    st.write("Vista parcial del dataframe unificado:")
    preview_cols = [
        "date",
        "city",
        "temp_mean",
        "temp_min",
        "temp_max",
        "precipitation_sum",
        "wind_speed_max",
        "is_forecast",
    ]
    existing_cols = [col for col in preview_cols if col in weather_df.columns]
    st.dataframe(weather_df[existing_cols].head(30), use_container_width=True)
