from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd
import requests

logger = logging.getLogger(__name__)


DAILY_VARIABLES = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "precipitation_sum",
    "wind_speed_10m_max",
    "weather_code",
]


API_RENAME_MAP = {
    "time": "date",
    "temperature_2m_mean": "temp_mean",
    "temperature_2m_min": "temp_min",
    "temperature_2m_max": "temp_max",
    "precipitation_sum": "precipitation_sum",
    "wind_speed_10m_max": "wind_speed_max",
    "weather_code": "weather_code",
}


def load_locations(path: str | Path) -> pd.DataFrame:
    """Carga ciudades y coordenadas objetivo para la zona central."""
    locations = pd.read_csv(path)

    required = {"city", "latitude", "longitude"}
    missing = required - set(locations.columns)
    if missing:
        raise ValueError(f"Faltan columnas en locations.csv: {sorted(missing)}")

    return locations


def _request_open_meteo_forecast(
    url: str,
    latitude: float,
    longitude: float,
    timezone: str,
    forecast_days: int,
    timeout: int = 30,
) -> dict[str, Any]:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": ",".join(DAILY_VARIABLES),
        "timezone": timezone,
        "forecast_days": forecast_days,
    }

    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


def extract_open_meteo_forecast(
    locations: pd.DataFrame,
    url: str,
    timezone: str = "America/Santiago",
    forecast_days: int = 7,
) -> pd.DataFrame:
    """Extrae pronóstico diario desde Open-Meteo para cada ciudad."""
    frames: list[pd.DataFrame] = []

    for row in locations.itertuples(index=False):
        logger.info("Consultando API Open-Meteo para %s", row.city)

        payload = _request_open_meteo_forecast(
            url=url,
            latitude=float(row.latitude),
            longitude=float(row.longitude),
            timezone=timezone,
            forecast_days=forecast_days,
        )

        daily = payload.get("daily")
        if not daily:
            raise ValueError(f"Respuesta API sin bloque `daily` para {row.city}")

        df_city = pd.DataFrame(daily).rename(columns=API_RENAME_MAP)
        df_city["city"] = row.city
        df_city["latitude"] = row.latitude
        df_city["longitude"] = row.longitude
        df_city["source"] = "open_meteo_api"
        df_city["pressure_mean"] = pd.NA

        frames.append(df_city)

    if not frames:
        raise ValueError("No se obtuvieron datos desde la API.")

    return pd.concat(frames, ignore_index=True)
