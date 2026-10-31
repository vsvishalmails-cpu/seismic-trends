"""Step 1: pull earthquake records from the USGS API, month by month.

USGS truncates very large result sets, so we chunk the request by month
and cache each month's raw response locally — re-running the pipeline
won't re-hit the API for months already downloaded.
"""
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import requests

import config


def _month_ranges(start_date: str, end_date: str):
    """Yield (chunk_start, chunk_end) ISO date strings, one per calendar month."""
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    cursor = date(start.year, start.month, 1)
    while cursor <= end:
        if cursor.month == 12:
            next_month = date(cursor.year + 1, 1, 1)
        else:
            next_month = date(cursor.year, cursor.month + 1, 1)

        chunk_start = max(cursor, start)
        chunk_end = min(next_month, end)
        yield chunk_start.isoformat(), chunk_end.isoformat()
        cursor = next_month


def _fetch_month(chunk_start: str, chunk_end: str) -> list[dict]:
    """Fetch one month of events, with one retry on failure."""
    params = {
        "format": "geojson",
        "starttime": chunk_start,
        "endtime": chunk_end,
        "minmagnitude": config.MIN_MAGNITUDE,
    }

    for attempt in (1, 2):
        response = requests.get(config.USGS_API_URL, params=params, timeout=30)
        if response.status_code == 200:
            return response.json()["features"]
        print(f"  attempt {attempt} failed ({chunk_start} to {chunk_end}): "
              f"HTTP {response.status_code}")

    print(f"  giving up on {chunk_start} to {chunk_end} after 2 attempts")
    return []


def _flatten_feature(feature: dict) -> dict:
    """Turn one GeoJSON feature into a flat dict matching the 26 source features."""
    props = feature["properties"]
    longitude, latitude, depth_km = feature["geometry"]["coordinates"]

    return {
        "id": feature["id"],
        "time": props.get("time"),
        "updated": props.get("updated"),
        "latitude": latitude,
        "longitude": longitude,
        "depth_km": depth_km,
        "mag": props.get("mag"),
        "magType": props.get("magType"),
        "place": props.get("place"),
        "status": props.get("status"),
        "tsunami": props.get("tsunami"),
        "sig": props.get("sig"),
        "net": props.get("net"),
        "nst": props.get("nst"),
        "dmin": props.get("dmin"),
        "rms": props.get("rms"),
        "gap": props.get("gap"),
        "magError": props.get("magError"),
        "depthError": props.get("depthError"),
        "magNst": props.get("magNst"),
        "locationSource": props.get("locationSource"),
        "magSource": props.get("magSource"),
        "types": props.get("types"),
        "ids": props.get("ids"),
        "sources": props.get("sources"),
        "type": props.get("type"),
        "alert": props.get("alert"),
    }


def fetch_all(start_date: str = config.START_DATE,
              end_date: str = config.END_DATE) -> pd.DataFrame:
    """Fetch every earthquake between start_date and end_date, cached per month."""
    config.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict] = []
    for chunk_start, chunk_end in _month_ranges(start_date, end_date):
        cache_path = config.RAW_DATA_DIR / f"{chunk_start[:7]}.json"

        if cache_path.exists():
            features = json.loads(cache_path.read_text())
        else:
            print(f"Fetching {chunk_start} to {chunk_end} ...")
            features = _fetch_month(chunk_start, chunk_end)
            cache_path.write_text(json.dumps(features))

        all_rows.extend(_flatten_feature(f) for f in features)

    df = pd.DataFrame(all_rows).drop_duplicates(subset="id")
    print(f"Fetched {len(df)} unique earthquake records "
          f"({start_date} to {end_date}, mag >= {config.MIN_MAGNITUDE}).")
    return df


if __name__ == "__main__":
    fetch_all()
