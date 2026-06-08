FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "etl.run_pipeline", "--historical-csv", "data/raw/historical_weather_central_chile.csv", "--output", "data/processed/weather_unified.parquet"]
