from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def load_weather_data(df: pd.DataFrame, output_path: str | Path) -> None:
    """Guarda dataframe procesado en parquet y CSV."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Guardando parquet en %s", output_path)
    df.to_parquet(output_path, index=False)

    csv_path = output_path.with_suffix(".csv")
    logger.info("Guardando CSV en %s", csv_path)
    df.to_csv(csv_path, index=False)
