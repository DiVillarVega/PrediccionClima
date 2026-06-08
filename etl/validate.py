from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = {
    "date",
    "city",
    "source",
    "temp_min",
    "temp_max",
    "precipitation_sum",
    "wind_speed_max",
}


NUMERIC_COLUMNS = [
    "temp_mean",
    "temp_min",
    "temp_max",
    "precipitation_sum",
    "wind_speed_max",
    "pressure_mean",
    "weather_code",
    "latitude",
    "longitude",
]


def validate_weather_schema(df: pd.DataFrame) -> None:
    """Valida esquema, tipos y reglas climáticas básicas."""
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {sorted(missing)}")

    if df.empty:
        raise ValueError("El dataframe está vacío.")

    if df["city"].isna().any():
        raise ValueError("Existen registros sin ciudad.")

    if df["date"].isna().any():
        raise ValueError("Existen registros sin fecha válida.")

    available_numeric = [col for col in NUMERIC_COLUMNS if col in df.columns]
    invalid_numeric = [
        col for col in available_numeric
        if not pd.api.types.is_numeric_dtype(df[col])
    ]
    if invalid_numeric:
        raise TypeError(f"Columnas no numéricas: {invalid_numeric}")

    invalid_temp_order = (
        df["temp_min"].notna()
        & df["temp_max"].notna()
        & (df["temp_min"] > df["temp_max"])
    )
    if invalid_temp_order.any():
        n = int(invalid_temp_order.sum())
        raise ValueError(f"Hay {n} filas con temp_min > temp_max.")

    negative_prcp = df["precipitation_sum"].notna() & (df["precipitation_sum"] < 0)
    if negative_prcp.any():
        n = int(negative_prcp.sum())
        raise ValueError(f"Hay {n} filas con precipitación negativa.")
