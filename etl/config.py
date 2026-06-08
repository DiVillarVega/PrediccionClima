from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Configuración externa del pipeline."""

    open_meteo_forecast_url: str
    timezone: str
    log_level: str
    locations_path: Path


def load_settings() -> Settings:
    """Carga variables de entorno y define valores por defecto reproducibles."""
    load_dotenv()

    return Settings(
        open_meteo_forecast_url=os.getenv(
            "OPEN_METEO_FORECAST_URL",
            "https://api.open-meteo.com/v1/forecast",
        ),
        timezone=os.getenv("TIMEZONE", "America/Santiago"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        locations_path=Path(os.getenv("LOCATIONS_PATH", "config/locations.csv")),
    )
