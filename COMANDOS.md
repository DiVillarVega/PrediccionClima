PARA RUNEAR EL DASHBOARD:
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\run_demo.ps1

------------------------------------------------------------

EJECUTAR ESTOS COMANDOS ANTES DE LA PRESENTACIÓN:

python scripts/download_meteostat_bulk_daily.py --start-year 2021 --end-year 2024 --output "data/raw/historical_weather_central_chile.csv"

python -m etl.run_pipeline --historical-csv "data/raw/historical_weather_central_chile.csv" --output "data/processed/weather_unified.parquet" --forecast-days 7

python -m ml.train_model --input "data/processed/weather_unified.parquet" --model-output "models/temp_max_next_day_model.joblib"

python -m ml.predict --input "data/processed/weather_unified.parquet" --model "models/temp_max_next_day_model.joblib" --output "data/processed/weather_predictions.parquet"

LUEGO SUBIR LOS SIGUIENTES ARCHIVOS AL GITHUB:
data/processed/weather_unified.parquet
data/processed/weather_unified.csv
data/processed/weather_predictions.parquet
models/temp_max_next_day_model.joblib
models/temp_max_next_day_metrics.json