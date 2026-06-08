from __future__ import annotations

import argparse
import gzip
import io
import math
import sqlite3
from pathlib import Path

import pandas as pd
import requests


STATIONS_DB_URL = "https://data.meteostat.net/stations.db"
DAILY_BULK_URL = "https://data.meteostat.net/daily/{year}/{station}.csv.gz"

DEFAULT_CITIES = {
    "Santiago": {"latitude": -33.4489, "longitude": -70.6693},
    "Valparaiso": {"latitude": -33.0472, "longitude": -71.6127},
    "Rancagua": {"latitude": -34.1708, "longitude": -70.7444},
    "Talca": {"latitude": -35.4264, "longitude": -71.6554},
    "Chillan": {"latitude": -36.6066, "longitude": -72.1034},
}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula distancia aproximada entre dos puntos geográficos."""
    radius = 6371.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )

    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def download_file(url: str, output_path: Path) -> None:
    """Descarga un archivo si no existe localmente."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        print(f"[OK] Ya existe: {output_path}")
        return

    print(f"[INFO] Descargando: {url}")
    response = requests.get(url, timeout=60)
    response.raise_for_status()

    output_path.write_bytes(response.content)
    print(f"[OK] Guardado en: {output_path}")


def load_chilean_stations(db_path: Path) -> pd.DataFrame:
    """Carga estaciones chilenas desde stations.db."""
    conn = sqlite3.connect(db_path)

    query = """
        SELECT
            s.id AS station_id,
            COALESCE(n.name, s.id) AS station_name,
            s.country,
            s.region,
            s.latitude,
            s.longitude,
            s.elevation,
            s.timezone
        FROM stations s
        LEFT JOIN names n
            ON s.id = n.station
            AND n.language = 'en'
        WHERE s.country = 'CL'
          AND s.latitude IS NOT NULL
          AND s.longitude IS NOT NULL
    """

    stations = pd.read_sql_query(query, conn)
    conn.close()

    if stations.empty:
        raise ValueError("No se encontraron estaciones chilenas en stations.db.")

    return stations


def nearest_station_candidates(
    stations: pd.DataFrame,
    latitude: float,
    longitude: float,
    top_n: int = 12,
) -> pd.DataFrame:
    """Obtiene las estaciones chilenas más cercanas a una ciudad."""
    df = stations.copy()

    df["distance_km"] = df.apply(
        lambda row: haversine_km(
            latitude,
            longitude,
            float(row["latitude"]),
            float(row["longitude"]),
        ),
        axis=1,
    )

    return df.sort_values("distance_km").head(top_n).reset_index(drop=True)


def fetch_daily_station_year(station_id: str, year: int) -> pd.DataFrame | None:
    """Descarga un año de datos diarios para una estación Meteostat."""
    url = DAILY_BULK_URL.format(year=year, station=station_id)

    try:
        response = requests.get(url, timeout=45)
    except requests.RequestException:
        return None

    if response.status_code == 404:
        return None

    if response.status_code != 200:
        return None

    try:
        with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as gz:
            df = pd.read_csv(gz)
    except Exception:
        return None

    if df.empty:
        return None

    return df


def build_city_dataset(
    city: str,
    city_latitude: float,
    city_longitude: float,
    stations: pd.DataFrame,
    start_year: int,
    end_year: int,
    top_n: int,
) -> pd.DataFrame:
    """Busca la mejor estación cercana y descarga datos diarios para la ciudad."""
    candidates = nearest_station_candidates(
        stations=stations,
        latitude=city_latitude,
        longitude=city_longitude,
        top_n=top_n,
    )

    best_df = None
    best_station = None
    best_rows = 0

    print(f"\n[INFO] Buscando estación para {city}...")

    for _, station in candidates.iterrows():
        station_id = station["station_id"]
        station_name = station["station_name"]
        distance_km = round(float(station["distance_km"]), 2)

        yearly_frames = []

        for year in range(start_year, end_year + 1):
            df_year = fetch_daily_station_year(station_id, year)
            if df_year is not None:
                yearly_frames.append(df_year)

        if not yearly_frames:
            print(f"  - Sin datos diarios: {station_id} | {station_name} | {distance_km} km")
            continue

        candidate_df = pd.concat(yearly_frames, ignore_index=True)
        candidate_rows = len(candidate_df)

        print(
            f"  - Candidato: {station_id} | {station_name} | "
            f"{distance_km} km | filas={candidate_rows}"
        )

        if candidate_rows > best_rows:
            best_rows = candidate_rows
            best_df = candidate_df
            best_station = station

    if best_df is None or best_station is None:
        raise ValueError(f"No se encontraron datos diarios útiles para {city}.")

    station_id = best_station["station_id"]
    station_name = best_station["station_name"]
    distance_km = round(float(best_station["distance_km"]), 2)

    print(
        f"[OK] {city}: usando estación {station_id} | "
        f"{station_name} | distancia={distance_km} km | filas={best_rows}"
    )

    df = best_df.copy()

    if "time" not in df.columns:
        raise ValueError(f"La estación {station_id} no trae columna `time`.")

    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(subset=["time"])

    df["city"] = city
    df["latitude"] = city_latitude
    df["longitude"] = city_longitude
    df["station_id"] = station_id
    df["station_name"] = station_name
    df["station_distance_km"] = distance_km

    # El pipeline actual espera `wspd`.
    # Si no existe `wspd`, usamos `wpgt` como respaldo si está disponible.
    if "wspd" not in df.columns and "wpgt" in df.columns:
        df["wspd"] = df["wpgt"]

    # Precipitación vacía se deja como 0 para evitar perder días completos.
    if "prcp" in df.columns:
        df["prcp"] = pd.to_numeric(df["prcp"], errors="coerce").fillna(0)

    expected_columns = [
        "time",
        "city",
        "latitude",
        "longitude",
        "station_id",
        "station_name",
        "station_distance_km",
        "tavg",
        "tmin",
        "tmax",
        "prcp",
        "wspd",
        "pres",
    ]

    for col in expected_columns:
        if col not in df.columns:
            df[col] = pd.NA

    return df[expected_columns]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Descarga dataset histórico real desde Meteostat Bulk Daily Data."
    )

    parser.add_argument("--start-year", type=int, default=2021)
    parser.add_argument("--end-year", type=int, default=2024)
    parser.add_argument(
        "--output",
        default="data/raw/historical_weather_central_chile.csv",
    )
    parser.add_argument(
        "--stations-db",
        default="data/raw/meteostat/stations.db",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=12,
        help="Cantidad de estaciones cercanas a probar por ciudad.",
    )

    args = parser.parse_args()

    output_path = Path(args.output)
    stations_db_path = Path(args.stations_db)

    download_file(STATIONS_DB_URL, stations_db_path)

    stations = load_chilean_stations(stations_db_path)

    all_frames = []

    for city, coords in DEFAULT_CITIES.items():
        city_df = build_city_dataset(
            city=city,
            city_latitude=coords["latitude"],
            city_longitude=coords["longitude"],
            stations=stations,
            start_year=args.start_year,
            end_year=args.end_year,
            top_n=args.top_n,
        )

        all_frames.append(city_df)

    final_df = pd.concat(all_frames, ignore_index=True)
    final_df = final_df.sort_values(["city", "time"]).reset_index(drop=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(output_path, index=False, encoding="utf-8")

    print("\n[OK] Dataset histórico real generado correctamente.")
    print(f"[OK] Archivo: {output_path}")
    print(f"[OK] Filas: {len(final_df)}")
    print(f"[OK] Ciudades: {final_df['city'].nunique()}")
    print(f"[OK] Rango fechas: {final_df['time'].min()} a {final_df['time'].max()}")
    print("\nResumen por ciudad:")
    print(final_df.groupby("city").size())


if __name__ == "__main__":
    main()