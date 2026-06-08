# Diccionario de datos inicial

## Variables finales del dataframe

| Variable | Tipo esperado | Unidad | Uso |
|---|---:|---|---|
| date | date | - | eje temporal |
| city | string | - | filtro geográfico |
| source | string | - | trazabilidad de fuente |
| latitude | float | grados | georreferenciación |
| longitude | float | grados | georreferenciación |
| temp_mean | float | °C | análisis/modelo |
| temp_min | float | °C | análisis/modelo |
| temp_max | float | °C | target recomendado inicial |
| precipitation_sum | float | mm/día | análisis/modelo de lluvia |
| wind_speed_max | float | km/h | análisis/modelo |
| pressure_mean | float | hPa | análisis/modelo si está disponible |
| weather_code | float | código | visualización de condición |
| year | int | - | feature temporal |
| month | int | - | feature temporal |
| day_of_year | int | - | feature temporal estacional |
| season | string | - | agrupación dashboard |
| is_forecast | bool | - | distingue histórico vs pronóstico |

## Target recomendado para el primer modelo

`temp_max_next_day`: temperatura máxima del día siguiente por ciudad.

Más adelante se crea con:

```python
df["temp_max_next_day"] = df.sort_values(["city", "date"]).groupby("city")["temp_max"].shift(-1)
```
