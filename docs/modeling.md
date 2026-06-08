# Modelo predictivo

## Objetivo

Predecir `target_temp_max_next_day`, es decir, la temperatura máxima del día siguiente por ciudad.

## Variables principales

- Ciudad
- Latitud y longitud
- Temperatura media, mínima y máxima
- Precipitación diaria
- Viento máximo
- Presión media
- Variables temporales cíclicas
- Lags del día anterior
- Promedios móviles de 3 días

## Modelo base

Se utiliza `RandomForestRegressor` dentro de un pipeline de Scikit-learn con:

- Imputación de valores numéricos mediante mediana.
- OneHotEncoding para la ciudad.
- Bosque aleatorio para capturar relaciones no lineales.

## Métricas

El entrenamiento exporta:

- MAE
- RMSE
- R²
- Cantidad de filas supervisadas

Archivo generado:

```text
models/temp_max_next_day_model.metrics.json
```

## Importante

El dataset `historical_weather_demo_synthetic.csv` sirve solo para desarrollo y demostración técnica.
Para la entrega final se debe reemplazar por un histórico real descargado desde Meteostat, NOAA u otra fuente confiable.
