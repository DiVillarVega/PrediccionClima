from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from ml.features import FEATURE_COLUMNS, TARGET_COLUMN, build_supervised_dataset


MIN_TRAINING_ROWS = 30


def load_dataframe(path: str | Path) -> pd.DataFrame:
    """Carga dataframe unificado desde Parquet o CSV."""
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {path}")

    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)

    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)

    raise ValueError("Formato no soportado. Usa .parquet o .csv")


def train_temperature_model(input_path: str | Path, model_path: str | Path) -> dict:
    """
    Entrena un modelo base para predecir temp_max del día siguiente.

    Modelo elegido:
    - RandomForestRegressor, robusto para relaciones no lineales y variables mixtas.
    """
    df = load_dataframe(input_path)
    model_df = build_supervised_dataset(df)

    if len(model_df) < MIN_TRAINING_ROWS:
        raise ValueError(
            f"Dataset insuficiente para entrenar: {len(model_df)} filas supervisadas. "
            f"Necesitamos al menos {MIN_TRAINING_ROWS}. "
            "Usa un histórico real de varios meses/años o el dataset demo extendido."
        )

    X = model_df[["city", *FEATURE_COLUMNS]]
    y = model_df[TARGET_COLUMN].astype(float)

    test_size = 0.2 if len(model_df) >= 80 else 0.3

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=42,
        shuffle=True,
    )

    numeric_features = FEATURE_COLUMNS
    categorical_features = ["city"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", SimpleImputer(strategy="median"), numeric_features),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ]
    )

    model = RandomForestRegressor(
        n_estimators=250,
        max_depth=10,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )

    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)

    metrics = {
        "rows_supervised": int(len(model_df)),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "mae": round(float(mean_absolute_error(y_test, y_pred)), 3),
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 3),
        "r2": round(float(r2_score(y_test, y_pred)), 3) if len(y_test) > 1 else None,
        "target": TARGET_COLUMN,
        "features": ["city", *FEATURE_COLUMNS],
    }

    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)

    artifact = {
        "pipeline": pipeline,
        "metrics": metrics,
        "feature_columns": FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
    }

    joblib.dump(artifact, model_path)

    metrics_path = model_path.with_suffix(".metrics.json")
    metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")

    return metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Entrenamiento modelo clima central")
    parser.add_argument(
        "--input",
        default="data/processed/weather_unified.parquet",
        help="Ruta del dataframe unificado.",
    )
    parser.add_argument(
        "--model-output",
        default="models/temp_max_next_day_model.joblib",
        help="Ruta donde se guardará el modelo.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    metrics = train_temperature_model(args.input, args.model_output)

    print("\nModelo entrenado correctamente.")
    print("Métricas:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
