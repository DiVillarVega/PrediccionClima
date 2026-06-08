Write-Host "Iniciando ClimaCentral AI..." -ForegroundColor Cyan

if (!(Test-Path ".venv")) {
    Write-Host "Creando entorno virtual..." -ForegroundColor Yellow
    python -m venv .venv
}

Write-Host "Activando entorno virtual..." -ForegroundColor Yellow
.\.venv\Scripts\Activate.ps1

Write-Host "Instalando dependencias..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Write-Host "Verificando archivos necesarios..." -ForegroundColor Yellow

if (!(Test-Path "data/processed/weather_unified.parquet")) {
    Write-Host "ERROR: No existe data/processed/weather_unified.parquet" -ForegroundColor Red
    exit
}

if (!(Test-Path "data/processed/weather_predictions.parquet")) {
    Write-Host "ERROR: No existe data/processed/weather_predictions.parquet" -ForegroundColor Red
    exit
}

Write-Host "Abriendo dashboard..." -ForegroundColor Green
streamlit run dashboards/app.py