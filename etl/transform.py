from __future__ import annotations

import numpy as np
import pandas as pd

from etl.validate import NUMERIC_COLUMNS, validate_weather_schema


FINAL_COLUMNS = [
    "date",
    "city",
    "source",
    "latitude",
    "longitude",
    "temp_mean",
    "temp_min",
    "temp_max",
    "precipitation_sum",
    "wind_speed_max",
    "pressure_mean",
    "weather_code",
    "year",
    "month",
    "day_of_year",
    "season",
    "is_forecast",
]


def _season_southern_hemisphere(month: int) -> str:
    if month in [12, 1, 2]:
        return "verano"
    if month in [3, 4, 5]:
        return "otono"
    if month in [6, 7, 8]:
        return "invierno"
    return "primavera"


def clean_weather_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza tipos, nombres y reglas comunes."""
    df = df.copy()

    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df["city"] = df["city"].astype(str).str.strip()

    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Completar temp_mean cuando venga ausente, usando promedio simple min/max.
    if "temp_mean" not in df.columns:
        df["temp_mean"] = np.nan

    mean_missing = df["temp_mean"].isna() & df["temp_min"].notna() & df["temp_max"].notna()
    df.loc[mean_missing, "temp_mean"] = (
        df.loc[mean_missing, "temp_min"] + df.loc[mean_missing, "temp_max"]
    ) / 2

    return df


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega variables temporales útiles para modelos y dashboards."""
    df = df.copy()
    date_series = pd.to_datetime(df["date"], errors="coerce")

    df["year"] = date_series.dt.year
    df["month"] = date_series.dt.month
    df["day_of_year"] = date_series.dt.dayofyear
    df["season"] = df["month"].apply(_season_southern_hemisphere)
    df["is_forecast"] = df["source"].eq("open_meteo_api")

    return df


def transform_weather_data(
    historical_df: pd.DataFrame,
    api_df: pd.DataFrame,
) -> pd.DataFrame:
    """Une dataset histórico + API y entrega dataframe analítico final."""
    historical_df = clean_weather_dataframe(historical_df)
    api_df = clean_weather_dataframe(api_df)

    df = pd.concat([historical_df, api_df], ignore_index=True, sort=False)
    df = add_time_features(df)

    for col in FINAL_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA

    df = df[FINAL_COLUMNS].sort_values(["city", "date", "source"]).reset_index(drop=True)

    validate_weather_schema(df)

    return df
