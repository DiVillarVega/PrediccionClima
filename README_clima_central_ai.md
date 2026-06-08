# ClimaCentral AI — Monitoreo y Predicción del Clima en la Zona Central de Chile

Proyecto académico de **Programación para la Ciencia de Datos** orientado a construir una solución end-to-end de análisis climático: extracción de datos desde múltiples fuentes, pipeline ETL, modelo predictivo y dashboard interactivo.

El producto simulado es **ClimaCentral AI**, una plataforma que integra datos históricos y pronósticos meteorológicos para visualizar condiciones climáticas y estimar la temperatura máxima del día siguiente en ciudades de la zona central de Chile.

---

## 1. Objetivo del proyecto

Construir una solución de ciencia de datos capaz de:

- Integrar datos climáticos desde **2 fuentes diferentes**:
  - Dataset histórico CSV desde **Meteostat Bulk Daily Data**.
  - API REST desde **Open-Meteo Forecast API**.
- Unificar ambas fuentes en un único dataframe analítico.
- Ejecutar un pipeline ETL reproducible.
- Entrenar un modelo de Machine Learning para predicción climática.
- Visualizar resultados en un dashboard interactivo desarrollado en Streamlit.
- Mantener una estructura de proyecto preparada para Git, Docker, documentación y defensa técnica.

---

## 2. Ciudades consideradas

El proyecto trabaja con cinco ciudades de la zona central de Chile:

| Ciudad | Latitud | Longitud | Región |
|---|---:|---:|---|
| Santiago | -33.4489 | -70.6693 | Metropolitana |
| Valparaiso | -33.0472 | -71.6127 | Valparaíso |
| Rancagua | -34.1708 | -70.7444 | O'Higgins |
| Talca | -35.4264 | -71.6554 | Maule |
| Chillan | -36.6066 | -72.1034 | Ñuble |

Archivo de configuración:

```text
config/locations.csv
```

---

## 3. Arquitectura general

```text
Meteostat Bulk Daily Data              Open-Meteo Forecast API
      Dataset CSV histórico                 API REST pronóstico
              │                                      │
              └───────────────┬──────────────────────┘
                              ↓
                       Pipeline ETL
                              ↓
               data/processed/weather_unified.parquet
                              ↓
                    Feature Engineering ML
                              ↓
             Modelo: temperatura máxima día siguiente
                              ↓
             data/processed/weather_predictions.parquet
                              ↓
                    Dashboard Streamlit
```

La idea central es que el usuario final **no elige entre dataset o API**. Ambas fuentes se transforman y consolidan previamente en una sola fuente analítica:

```text
weather_unified.parquet
```

La columna `source` se mantiene solo para trazabilidad técnica.

---

## 4. Estructura del proyecto

```text
clima_central_chile/
├── api/
│   └── README.md
├── config/
│   └── locations.csv
├── dashboards/
│   ├── README.md
│   └── app.py
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── docs/
│   ├── data_dictionary.md
│   ├── modeling.md
│   └── unification_strategy.md
├── etl/
│   ├── extract_api.py
│   ├── extract_dataset.py
│   ├── load.py
│   ├── run_pipeline.py
│   ├── transform.py
│   └── validate.py
├── logs/
├── ml/
│   ├── features.py
│   ├── predict.py
│   └── train_model.py
├── models/
├── scripts/
│   ├── download_meteostat_bulk_daily.py
│   └── make_demo_historical_dataset.py
├── tests/
│   └── test_transform.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

---

## 5. Requisitos

- Python 3.11 o superior.
- Git.
- Conexión a internet para descargar datos y consultar la API.
- PowerShell en Windows.
- Opcional: Docker Desktop.

---

## 6. Instalación desde GitHub ZIP

Descargar el proyecto desde GitHub como `.zip`, descomprimirlo y entrar a la carpeta del proyecto.

En PowerShell:

```powershell
cd "C:\ruta\donde\dejaste\clima_central_chile"
```

Crear entorno virtual:

```powershell
python -m venv .venv
```

Activar entorno virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea la activación:

```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\.venv\Scripts\Activate.ps1
```

Instalar dependencias:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Crear archivo `.env` desde el ejemplo:

```powershell
Copy-Item .env.example .env -Force
```

---

## 7. Configuración de ciudades

Verificar que el archivo `config/locations.csv` tenga este contenido:

```csv
city,latitude,longitude,region
Santiago,-33.4489,-70.6693,Metropolitana
Valparaiso,-33.0472,-71.6127,Valparaiso
Rancagua,-34.1708,-70.7444,O'Higgins
Talca,-35.4264,-71.6554,Maule
Chillan,-36.6066,-72.1034,Nuble
```

---

## 8. Descargar dataset real desde Meteostat

El proyecto usa Meteostat Bulk Daily Data como fuente histórica.

Ejecutar:

```powershell
python scripts/download_meteostat_bulk_daily.py --start-year 2021 --end-year 2024 --output "data/raw/historical_weather_central_chile.csv"
```

Este script realiza lo siguiente:

1. Descarga la metadata de estaciones meteorológicas.
2. Busca estaciones chilenas cercanas a las cinco ciudades del proyecto.
3. Descarga archivos diarios por estación y año.
4. Normaliza columnas relevantes.
5. Genera un único CSV histórico.

Archivo esperado:

```text
data/raw/historical_weather_central_chile.csv
```

---

## 9. Ejecutar pipeline ETL

Una vez descargado el dataset histórico real, ejecutar:

```powershell
python -m etl.run_pipeline --historical-csv "data/raw/historical_weather_central_chile.csv" --output "data/processed/weather_unified.parquet" --forecast-days 7
```

Salida esperada:

```text
data/processed/weather_unified.parquet
data/processed/weather_unified.csv
```

El pipeline hace:

1. Lee el dataset histórico CSV.
2. Consulta la API REST de Open-Meteo.
3. Normaliza columnas de ambas fuentes.
4. Valida esquema, fechas, nulos y rangos.
5. Une los datos en una sola tabla analítica.
6. Exporta resultados en formato Parquet y CSV.

---

## 10. Horizonte de pronóstico

Por defecto se usan 7 días:

```powershell
--forecast-days 7
```

Para extender el horizonte operativo hasta 16 días:

```powershell
python -m etl.run_pipeline --historical-csv "data/raw/historical_weather_central_chile.csv" --output "data/processed/weather_unified.parquet" --forecast-days 16
```

Después de cambiar el horizonte de pronóstico, se deben regenerar las predicciones.

---

## 11. Entrenar modelo predictivo

El modelo predice:

```text
target_temp_max_next_day
```

Es decir:

> Temperatura máxima estimada para el día siguiente.

Entrenar modelo:

```powershell
python -m ml.train_model --input "data/processed/weather_unified.parquet" --model-output "models/temp_max_next_day_model.joblib"
```

Salida esperada:

```text
models/temp_max_next_day_model.joblib
models/temp_max_next_day_metrics.json
```

El modelo base utilizado es un `RandomForestRegressor`, adecuado como primera aproximación para datos tabulares con relaciones no lineales.

---

## 12. Generar predicciones

Después de entrenar el modelo:

```powershell
python -m ml.predict --input "data/processed/weather_unified.parquet" --model "models/temp_max_next_day_model.joblib" --output "data/processed/weather_predictions.parquet"
```

Salida esperada:

```text
data/processed/weather_predictions.parquet
```

Importante:

- El modelo se entrena principalmente con datos históricos observados.
- Las predicciones operativas se generan sobre registros futuros provenientes de la API.
- En el dashboard, `date` representa la fecha base y `pred_temp_max_next_day` representa la estimación para el día siguiente.

---

## 13. Ejecutar dashboard

```powershell
streamlit run dashboards/app.py
```

Streamlit abrirá una URL local similar a:

```text
http://localhost:8501
```

---

## 14. Controles del dashboard

El dashboard está diseñado para que el usuario interactúe con una fuente ya unificada.

### Ciudad

Permite elegir una ciudad:

```text
Santiago
Valparaiso
Rancagua
Talca
Chillan
```

Todos los gráficos y métricas se actualizan según la ciudad seleccionada.

### Rango de fechas

Permite filtrar el periodo visualizado.

Sirve para analizar:

- Histórico completo.
- Un año específico.
- Últimos meses.
- Zona donde termina el histórico y comienza el pronóstico.

### Indicador climático

Permite elegir la variable principal del gráfico:

```text
temp_max
temp_mean
temp_min
precipitation_sum
wind_speed_max
```

---

## 15. Visualizaciones del dashboard

### Métricas superiores

Muestran valores recientes para la ciudad seleccionada:

- Temperatura máxima reciente.
- Temperatura mínima reciente.
- Precipitación reciente.
- Riesgo de lluvia.

El riesgo de lluvia se calcula como regla de negocio:

```text
precipitation_sum >= 10 mm → Alto
precipitation_sum >= 2 mm  → Medio
precipitation_sum < 2 mm   → Bajo
```

### Serie climática unificada

Gráfico principal del dashboard.

Muestra la evolución temporal del indicador seleccionado, usando el dataframe unificado:

```text
weather_unified.parquet
```

Este gráfico no separa visualmente dataset y API, porque ambas fuentes ya fueron integradas por el ETL.

### Inicio del pronóstico

El dashboard marca visualmente el punto donde terminan los datos históricos y comienzan los datos provenientes de la API REST.

Esto permite defender que el sistema combina:

```text
histórico real + pronóstico operativo
```

### Predicción operativa

Compara:

```text
temp_max
pred_temp_max_next_day
```

Interpretación:

- `temp_max`: temperatura máxima base entregada por la API para una fecha.
- `pred_temp_max_next_day`: temperatura máxima estimada por el modelo para el día siguiente.

### Tabla de predicciones

Muestra los valores exactos usados por el dashboard:

```text
date
city
temp_min
temp_max
pred_temp_max_next_day
precipitation_sum
rain_risk
```

### Trazabilidad técnica

Sección pensada para defensa técnica, no para usuario final.

Permite revisar cuántos registros vienen desde:

```text
meteostat_dataset
open_meteo_api
```

La trazabilidad demuestra que sí hubo integración de fuentes, pero no se presenta como una elección para el usuario final.

---

## 16. Ejecutar tests

```powershell
pytest
```

También se puede ejecutar:

```powershell
pytest tests/
```

Los tests sirven para evidenciar validaciones básicas del pipeline y transformaciones.

---

## 17. Ejecución completa recomendada

Para correr todo desde cero:

```powershell
python scripts/download_meteostat_bulk_daily.py --start-year 2021 --end-year 2024 --output "data/raw/historical_weather_central_chile.csv"

python -m etl.run_pipeline --historical-csv "data/raw/historical_weather_central_chile.csv" --output "data/processed/weather_unified.parquet" --forecast-days 7

python -m ml.train_model --input "data/processed/weather_unified.parquet" --model-output "models/temp_max_next_day_model.joblib"

python -m ml.predict --input "data/processed/weather_unified.parquet" --model "models/temp_max_next_day_model.joblib" --output "data/processed/weather_predictions.parquet"

streamlit run dashboards/app.py
```

---

## 18. Docker

Construir imagen:

```powershell
docker build -f docker/Dockerfile -t clima-central-ai .
```

Ejecutar contenedor:

```powershell
docker run -p 8501:8501 clima-central-ai
```

O usando Docker Compose:

```powershell
docker compose -f docker/docker-compose.yml up --build
```

---

## 19. Archivos que no deberían subirse a GitHub

No subir:

```text
.venv/
__pycache__/
data/raw/*.csv
data/processed/*.csv
data/processed/*.parquet
models/*.joblib
logs/*.log
.env
```

Sí subir:

```text
etl/
ml/
dashboards/
docs/
tests/
docker/
config/
requirements.txt
.env.example
README.md
```

---

## 20. Flujo de trabajo recomendado en Git

Crear ramas por tarea:

```powershell
git checkout -b feature/dashboard
git checkout -b feature/etl-validations
git checkout -b feature/model-improvements
git checkout -b docs/readme-update
```

Commits recomendados:

```powershell
git add .
git commit -m "feat: add unified dashboard"
git commit -m "feat: integrate meteostat historical dataset"
git commit -m "docs: update execution guide"
git commit -m "test: add ETL transformation tests"
```

Antes de hacer merge:

```powershell
pytest
python -m etl.run_pipeline --historical-csv "data/raw/historical_weather_central_chile.csv" --output "data/processed/weather_unified.parquet" --forecast-days 7
```

---

## 21. Rol de cada componente

| Componente | Rol |
|---|---|
| `etl/` | Extrae, transforma, valida y carga datos |
| `ml/` | Genera features, entrena modelo y produce predicciones |
| `dashboards/` | Visualiza datos y predicciones |
| `config/` | Centraliza ciudades y coordenadas |
| `docs/` | Documentación técnica |
| `tests/` | Validación automatizada |
| `docker/` | Containerización y despliegue |
| `data/` | Datos crudos y procesados |
| `models/` | Modelos entrenados |

---

## 22. Cómo explicar el proyecto en la defensa

Frase recomendada:

> ClimaCentral AI integra datos históricos de Meteostat y pronósticos de Open-Meteo en una única base analítica. Sobre esa base se ejecuta un modelo predictivo que estima la temperatura máxima del día siguiente para cinco ciudades de la zona central de Chile. El dashboard permite monitorear variables climáticas, visualizar el inicio del pronóstico y revisar predicciones operativas sin que el usuario tenga que interactuar directamente con las fuentes originales.

Puntos clave para defender:

- El usuario consume una fuente unificada, no dos fuentes separadas.
- El ETL mantiene trazabilidad técnica mediante la columna `source`.
- El modelo se entrena con histórico observado.
- La API entrega datos recientes/futuros para operación del dashboard.
- El pipeline es reproducible mediante comandos, entorno virtual y Docker.
- El proyecto sigue una estructura profesional compatible con Git y despliegue.

---

## 23. Fuentes de datos

### Meteostat Bulk Daily Data

Fuente usada para datos históricos diarios por estación meteorológica.

- Uso en el proyecto: entrenamiento del modelo y análisis histórico.
- Formato: CSV comprimido por estación y año.
- Archivo final generado: `data/raw/historical_weather_central_chile.csv`.

### Open-Meteo Forecast API

Fuente usada para pronóstico climático.

- Uso en el proyecto: registros futuros para predicción operativa.
- Horizonte usado en demo: 7 días.
- Horizonte máximo recomendado en el proyecto: 16 días.
- No requiere API key para el prototipo académico.

---

## 24. Troubleshooting

### Error: `Activate.ps1 no se reconoce`

Significa que no existe el entorno virtual en esa carpeta.

Solución:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Error de permisos al activar entorno virtual

Solución:

```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\.venv\Scripts\Activate.ps1
```

### Error: no existe `weather_unified.parquet`

Primero ejecutar el ETL:

```powershell
python -m etl.run_pipeline --historical-csv "data/raw/historical_weather_central_chile.csv" --output "data/processed/weather_unified.parquet" --forecast-days 7
```

### Error: no existe `weather_predictions.parquet`

Primero entrenar y predecir:

```powershell
python -m ml.train_model --input "data/processed/weather_unified.parquet" --model-output "models/temp_max_next_day_model.joblib"

python -m ml.predict --input "data/processed/weather_unified.parquet" --model "models/temp_max_next_day_model.joblib" --output "data/processed/weather_predictions.parquet"
```

### El dashboard abre pero no muestra predicciones

Verificar que exista:

```text
data/processed/weather_predictions.parquet
```

y luego reiniciar Streamlit.

---

## 25. Estado actual del proyecto

El proyecto queda listo para que el equipo continúe puliendo:

- Diseño visual del dashboard.
- Storytelling tipo producto.
- Mejoras en gráficos.
- Secciones ejecutivas, técnicas y operativas.
- Docker final.
- Documentación final y presentación.
