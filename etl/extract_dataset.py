from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


METEOSTAT_RENAME_MAP = {
    "time": "date",
    "tavg": "temp_mean",
    "tmin": "temp_min",
    "tmax": "temp_max",
    "prcp": "precipitation_sum",
    "wspd": "wind_speed_max",
    "pres": "pressure_mean",
}


def extract_historical_dataset(path: str | Path) -> pd.DataFrame:
    """
    Extrae dataset histórico desde CSV o Excel.

    Formatos soportados:
    - CSV Meteostat enriquecido con columna `city`.
    - Excel con columnas equivalentes.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"No existe el dataset histórico: {path}. "
            "Descarga/prepara el archivo en data/raw/ y vuelve a ejecutar."
        )

    logger.info("Leyendo dataset histórico desde %s", path)

    if path.suffix.lower() in {".xlsx", ".xls"}:
        df = pd.read_excel(path)
    elif path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    else:
        raise ValueError("Formato no soportado. Usa .csv, .xlsx o .xls")

    df = df.rename(columns=METEOSTAT_RENAME_MAP)
    df["source"] = "historical_csv"

    if "city" not in df.columns:
        raise ValueError(
            "El dataset histórico debe incluir columna `city` "
            "para poder unificarlo con los datos de API."
        )

    return df
