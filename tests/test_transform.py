import pandas as pd

from etl.transform import transform_weather_data


def test_transform_weather_data_adds_expected_columns():
    historical = pd.DataFrame(
        {
            "date": ["2024-01-01"],
            "city": ["Santiago"],
            "source": ["historical_csv"],
            "temp_mean": [22.0],
            "temp_min": [15.0],
            "temp_max": [29.0],
            "precipitation_sum": [0.0],
            "wind_speed_max": [18.0],
            "pressure_mean": [1012.0],
        }
    )

    api = pd.DataFrame(
        {
            "date": ["2024-01-02"],
            "city": ["Santiago"],
            "latitude": [-33.4489],
            "longitude": [-70.6693],
            "source": ["open_meteo_api"],
            "temp_mean": [23.0],
            "temp_min": [16.0],
            "temp_max": [30.0],
            "precipitation_sum": [0.0],
            "wind_speed_max": [20.0],
            "weather_code": [0],
            "pressure_mean": [pd.NA],
        }
    )

    result = transform_weather_data(historical, api)

    assert len(result) == 2
    assert {"year", "month", "day_of_year", "season", "is_forecast"}.issubset(result.columns)
    assert result["city"].nunique() == 1
    assert result.loc[result["source"].eq("open_meteo_api"), "is_forecast"].all()
