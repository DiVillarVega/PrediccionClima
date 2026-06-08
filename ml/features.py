from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


FEATURE_COLUMNS = [
    "latitude",
    "longitude",
    "temp_mean",
    "temp_min",
    "temp_max",
    "precipitation_sum",
    "wind_speed_max",
    "pressure_mean",
    "month_sin",
    "month_cos",
    "day_sin",
    "day_cos",
    "temp_max_lag_1",
    "temp_min_lag_1",
    "precipitation_lag_1",
    "temp_max_roll_3",
    "precipitation_roll_3",
]

TARGET_COLUMN = "target_temp_max_next_day"


@dataclass(frozen=True)
class FeatureConfig:
    """Configuración de variables para entrenamiento/predicción."""

    feature_columns: list[str]
    target_column: str = TARGET_COLUMN


def _add_cyclical_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Codifica mes y día del año como variables cíclicas."""
    df = df.copy()
    date_series = pd.to_datetime(df["date"], errors="coerce")

    month = date_series.dt.month.fillna(1).astype(int)
    day = date_series.dt.dayofyear.fillna(1).astype(int)

    df["month_sin"] = np.sin(2 * np.pi * month / 12)
    df["month_cos"] = np.cos(2 * np.pi * month / 12)
    df["day_sin"] = np.sin(2 * np.pi * day / 365)
    df["day_cos"] = np.cos(2 * np.pi * day / 365)

    return df


def build_supervised_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte la serie climática diaria en un dataset supervisado.

    Target:
    - target_temp_max_next_day: temperatura máxima del día siguiente por ciudad.
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values(["city", "date"]).reset_index(drop=True)

    # Entrenamos solo con datos históricos reales/csv, no con pronósticos de API.
    if "is_forecast" in df.columns:
        df = df[~df["is_forecast"].astype(bool)].copy()

    df = _add_cyclical_time_features(df)

    grouped = df.groupby("city", group_keys=False)

    df["temp_max_lag_1"] = grouped["temp_max"].shift(1)
    df["temp_min_lag_1"] = grouped["temp_min"].shift(1)
    df["precipitation_lag_1"] = grouped["precipitation_sum"].shift(1)

    df["temp_max_roll_3"] = grouped["temp_max"].transform(
        lambda s: s.shift(1).rolling(window=3, min_periods=1).mean()
    )
    df["precipitation_roll_3"] = grouped["precipitation_sum"].transform(
        lambda s: s.shift(1).rolling(window=3, min_periods=1).mean()
    )

    df[TARGET_COLUMN] = grouped["temp_max"].shift(-1)

    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan

    model_df = df[["date", "city", *FEATURE_COLUMNS, TARGET_COLUMN]].copy()
    model_df = model_df.dropna(subset=[TARGET_COLUMN, "temp_max", "temp_min"])

    return model_df


def build_prediction_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Genera features para filas futuras/pronosticadas.

    Usa la serie completa ordenada por ciudad; las variables lag se calculan
    con el registro inmediatamente anterior disponible.
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values(["city", "date", "source"]).reset_index(drop=True)
    df = _add_cyclical_time_features(df)

    grouped = df.groupby("city", group_keys=False)

    df["temp_max_lag_1"] = grouped["temp_max"].shift(1)
    df["temp_min_lag_1"] = grouped["temp_min"].shift(1)
    df["precipitation_lag_1"] = grouped["precipitation_sum"].shift(1)

    df["temp_max_roll_3"] = grouped["temp_max"].transform(
        lambda s: s.shift(1).rolling(window=3, min_periods=1).mean()
    )
    df["precipitation_roll_3"] = grouped["precipitation_sum"].transform(
        lambda s: s.shift(1).rolling(window=3, min_periods=1).mean()
    )

    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan

    return df
