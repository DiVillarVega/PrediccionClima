from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from ml.features import FEATURE_COLUMNS, build_prediction_features


def load_dataframe(path: str | Path) -> pd.DataFrame:
    path = Path(path)

    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)

    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)

    raise ValueError("Formato no soportado. Usa .parquet o .csv")


def predict_forecast_temperatures(
    input_path: str | Path,
    model_path: str | Path,
    output_path: str | Path,
) -> pd.DataFrame:
    """Aplica el modelo entrenado sobre filas de pronóstico API."""
    df = load_dataframe(input_path)
    features_df = build_prediction_features(df)

    forecast_df = features_df[features_df["is_forecast"].astype(bool)].copy()

    if forecast_df.empty:
        raise ValueError("No hay filas de pronóstico para predecir.")

    model_path = Path(model_path)
    if not model_path.exists():
        raise FileNotFoundError(
            f"No existe el modelo: {model_path}. Ejecuta primero ml.train_model."
        )

    artifact = joblib.load(model_path)
    pipeline = artifact["pipeline"]

    X_pred = forecast_df[["city", *FEATURE_COLUMNS]]
    forecast_df["pred_temp_max_next_day"] = pipeline.predict(X_pred).round(2)

    # Regla de negocio simple para dashboard: alerta por lluvia.
    forecast_df["rain_risk"] = np.select(
        [
            forecast_df["precipitation_sum"].fillna(0) >= 10,
            forecast_df["precipitation_sum"].fillna(0) >= 2,
        ],
        ["alto", "medio"],
        default="bajo",
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.suffix.lower() == ".parquet":
        forecast_df.to_parquet(output_path, index=False)
        forecast_df.to_csv(output_path.with_suffix(".csv"), index=False)
    else:
        forecast_df.to_csv(output_path, index=False)

    return forecast_df


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generar predicciones climáticas")
    parser.add_argument(
        "--input",
        default="data/processed/weather_unified.parquet",
        help="Dataframe unificado generado por el ETL.",
    )
    parser.add_argument(
        "--model",
        default="models/temp_max_next_day_model.joblib",
        help="Modelo entrenado.",
    )
    parser.add_argument(
        "--output",
        default="data/processed/weather_predictions.parquet",
        help="Salida de predicciones.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    predictions = predict_forecast_temperatures(args.input, args.model, args.output)
    print(f"Predicciones generadas: {len(predictions)} filas")
    print(predictions[["date", "city", "temp_max", "pred_temp_max_next_day", "rain_risk"]].head(20))
