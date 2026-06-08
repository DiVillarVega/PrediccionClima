from __future__ import annotations

import argparse
import logging
from pathlib import Path

from etl.config import load_settings
from etl.extract_api import extract_open_meteo_forecast, load_locations
from etl.extract_dataset import extract_historical_dataset
from etl.load import load_weather_data
from etl.logging_utils import setup_logging
from etl.transform import transform_weather_data

logger = logging.getLogger(__name__)


def run_pipeline(
    historical_csv: str | Path,
    output: str | Path,
    forecast_days: int = 7,
) -> None:
    settings = load_settings()
    setup_logging(settings.log_level)

    logger.info("Iniciando pipeline ETL clima zona central")

    locations = load_locations(settings.locations_path)
    historical_df = extract_historical_dataset(historical_csv)
    api_df = extract_open_meteo_forecast(
        locations=locations,
        url=settings.open_meteo_forecast_url,
        timezone=settings.timezone,
        forecast_days=forecast_days,
    )

    unified_df = transform_weather_data(historical_df, api_df)
    load_weather_data(unified_df, output)

    logger.info(
        "Pipeline finalizado. Filas=%s | Ciudades=%s | Rango=%s a %s",
        len(unified_df),
        unified_df["city"].nunique(),
        unified_df["date"].min(),
        unified_df["date"].max(),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pipeline ETL clima zona central Chile")
    parser.add_argument(
        "--historical-csv",
        required=True,
        help="Ruta del dataset histórico CSV/Excel.",
    )
    parser.add_argument(
        "--output",
        default="data/processed/weather_unified.parquet",
        help="Ruta de salida parquet.",
    )
    parser.add_argument(
        "--forecast-days",
        type=int,
        default=7,
        help="Días de pronóstico a consultar en Open-Meteo.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(
        historical_csv=args.historical_csv,
        output=args.output,
        forecast_days=args.forecast_days,
    )
