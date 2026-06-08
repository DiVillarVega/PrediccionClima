from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


CITY_CONFIG = {
    "Santiago": {"lat": -33.4489, "lon": -70.6693, "base": 21.5, "amp": 8.5, "rain_bias": 0.75},
    "Valparaiso": {"lat": -33.0472, "lon": -71.6127, "base": 17.0, "amp": 4.0, "rain_bias": 0.95},
    "Rancagua": {"lat": -34.1708, "lon": -70.7444, "base": 20.5, "amp": 8.0, "rain_bias": 0.8},
    "Talca": {"lat": -35.4264, "lon": -71.6554, "base": 19.0, "amp": 8.8, "rain_bias": 1.1},
}


def build_demo_dataset(start: str, end: str, output: str | Path) -> pd.DataFrame:
    """
    Crea un dataset demo sintético para probar ETL + modelo + dashboard.

    No usar como evidencia final de datos reales.
    Sirve para desarrollo mientras se descarga el histórico real.
    """
    rng = np.random.default_rng(42)
    dates = pd.date_range(start=start, end=end, freq="D")

    rows = []

    for city, cfg in CITY_CONFIG.items():
        for date in dates:
            doy = date.dayofyear

            # Hemisferio sur: mayor temperatura cerca de enero/febrero.
            seasonal = np.cos(2 * np.pi * (doy - 20) / 365)
            temp_mean = cfg["base"] + cfg["amp"] * seasonal + rng.normal(0, 1.4)

            temp_min = temp_mean - rng.uniform(4.5, 8.5)
            temp_max = temp_mean + rng.uniform(4.5, 9.5)

            # Más lluvia en invierno.
            winter_factor = max(0, -seasonal)
            rain_chance = min(0.75, 0.08 + 0.55 * winter_factor * cfg["rain_bias"])
            precipitation = rng.gamma(1.8, 5.0) if rng.random() < rain_chance else 0.0

            wind = max(4, rng.normal(18, 5))
            pressure = rng.normal(1013, 5)

            rows.append(
                {
                    "date": date.date().isoformat(),
                    "city": city,
                    "latitude": cfg["lat"],
                    "longitude": cfg["lon"],
                    "temp_mean": round(temp_mean, 1),
                    "temp_min": round(temp_min, 1),
                    "temp_max": round(temp_max, 1),
                    "precipitation_sum": round(float(precipitation), 1),
                    "wind_speed_max": round(float(wind), 1),
                    "pressure_mean": round(float(pressure), 1),
                }
            )

    df = pd.DataFrame(rows)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    return df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crear dataset demo sintético")
    parser.add_argument("--start", default="2021-01-01")
    parser.add_argument("--end", default="2024-12-31")
    parser.add_argument(
        "--output",
        default="data/raw/historical_weather_demo_synthetic.csv",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    df = build_demo_dataset(args.start, args.end, args.output)
    print(f"Dataset demo creado: {args.output}")
    print(f"Filas: {len(df)} | Ciudades: {df['city'].nunique()}")
