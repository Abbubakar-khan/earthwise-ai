"""NASA POWER daily point API client. Saves raw JSON metadata and a normalized CSV."""
from __future__ import annotations
import json
from pathlib import Path
import requests
import pandas as pd

API_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

def fetch_daily(city: str, latitude: float, longitude: float,
                start: str = "20010101", end: str = "20251231",
                parameters: tuple[str, ...] = ("T2M", "PRECTOTCORR"),
                timeout: int = 120) -> tuple[pd.DataFrame, dict]:
    params = {
        "parameters": ",".join(parameters),
        "community": "AG",
        "longitude": longitude,
        "latitude": latitude,
        "start": start,
        "end": end,
        "format": "JSON",
        "time-standard": "UTC",
    }
    response = requests.get(API_URL, params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    try:
        parameter_data = payload["properties"]["parameter"]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"Unexpected NASA POWER response: {str(payload)[:500]}") from exc

    df = pd.DataFrame(parameter_data)
    df.index.name = "date"
    df = df.reset_index()
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d", errors="coerce")
    df["city"] = city
    for col in parameters:
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            # NASA POWER uses -999 (and sometimes -999.0) as missing sentinel.
            df.loc[df[col] <= -900, col] = float("nan")

    metadata = payload.get("header", {})
    metadata.update({
        "city": city, "latitude": latitude, "longitude": longitude,
        "requested_start": start, "requested_end": end,
        "parameters": list(parameters), "api_url": response.url,
        "retrieved_utc": pd.Timestamp.now(tz="UTC").isoformat(),
    })
    return df, metadata

def save_city_data(df: pd.DataFrame, metadata: dict, city_slug: str,
                   base_dir: str | Path = "data") -> tuple[Path, Path]:
    base = Path(base_dir)
    raw_dir, processed_dir = base / "raw", base / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    csv_path = raw_dir / f"{city_slug}_nasa_power_daily.csv"
    meta_path = raw_dir / f"{city_slug}_nasa_power_metadata.json"
    df.to_csv(csv_path, index=False)
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return csv_path, meta_path
