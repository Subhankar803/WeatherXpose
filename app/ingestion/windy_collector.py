"""
Windy Point Forecast + Webcams collector.

Point Forecast is used mainly as a VERIFICATION signal (see
services/scoring.py -> check_windy_rainfall), not as an incident source
by itself — Windy never reports "flood" or "incident", only rainfall/
wind/temperature model numbers. Webcams are fetched opportunistically
(best-effort) since coverage over India is sparse.

Keys are read from app/config.py -> settings, which loads them from
.env. Leave WINDY_API_KEY blank in .env until you have it; every
function below fails safely (returns None / empty list) if the key
is missing, instead of crashing the whole ingestion run.
"""
import requests

from app.config import settings
from app.ingestion.base_collector import BaseCollector
from app.services.cache_service import get_cached_telemetry, set_cached_telemetry

POINT_FORECAST_URL = "https://api.windy.com/api/point-forecast/v2"
WEBCAMS_URL = "https://api.windy.com/webcams/api/v3/webcams"


def get_point_forecast(lat: float, lon: float, model: str = "gfs") -> dict | None:
    """
    Fetches raw rainfall/wind/temp model data for a coordinate.
    Caches response for 30 minutes to prevent API hammering and score jitter.
    """
    cache_key = f"windy_forecast:{round(lat, 2)}_{round(lon, 2)}_{model}"
    cached = get_cached_telemetry(cache_key)
    if cached is not None:
        return cached

    if not settings.windy_api_key:
        return None  # key not set yet — fail safe, don't crash ingestion

    payload = {
        "lat": lat,
        "lon": lon,
        "model": model,
        "parameters": ["temp", "wind", "rh", "pressure", "precip"],
        "levels": ["surface"],
        "key": settings.windy_api_key,
    }
    try:
        response = requests.post(POINT_FORECAST_URL, json=payload, timeout=12)
        response.raise_for_status()
        data = response.json()
        set_cached_telemetry(cache_key, data, ttl_seconds=1800)
        return data
    except requests.exceptions.RequestException as e:
        print(f"[windy_collector] point forecast error: {e}")
        return None


def get_nearby_webcams(lat: float, lon: float, radius_km: int = 50, limit: int = 5) -> list[dict]:
    """
    Best-effort: returns nearby public webcams, or an empty list if
    none exist near this coordinate (common in India outside major cities).
    """
    if not settings.windy_api_key:
        return []

    headers = {"x-windy-api-key": settings.windy_api_key}
    params = {
        "nearby": f"{lat},{lon},{radius_km}",
        "include": "images,location,urls",
        "limit": limit,
    }
    try:
        response = requests.get(WEBCAMS_URL, headers=headers, params=params, timeout=12)
        response.raise_for_status()
        return response.json().get("webcams", [])
    except requests.exceptions.RequestException as e:
        print(f"[windy_collector] webcams error: {e}")
        return []


class WindyCollector(BaseCollector):
    """
    Windy is NOT a content-collection source (it never mentions
    incidents), so .fetch() intentionally returns []. This class exists
    only so verification_engine.py has a single, consistent place to
    call get_point_forecast() from.
    """
    name = "windy"

    def fetch(self) -> list[dict]:
        return []


def check_windy_strong_hint(lat: float, lon: float, event_type: str = "rainfall") -> bool:
    """
    Evaluates whether Windy point forecast provides a strong hint for the claimed weather incident.
    Used by scoring.py (Windy check: min 5 pts baseline, max 15 pts strong hint).
    Caches evaluation for 30 minutes to guarantee deterministic scoring across repeated submissions.
    """
    hint_key = f"windy_hint:{round(lat, 2)}_{round(lon, 2)}_{(event_type or '').lower()}"
    cached_hint = get_cached_telemetry(hint_key)
    if cached_hint is not None:
        return bool(cached_hint)

    forecast = get_point_forecast(lat, lon)
    if not forecast:
        set_cached_telemetry(hint_key, False, ttl_seconds=1800)
        return False

    data = forecast.get("data", forecast)
    precip_raw = data.get("past3hprecip-surface") or data.get("precip-surface") or [0]
    if isinstance(precip_raw, list):
        # Windy model past3hprecip can be in meters (e.g. 0.0016m = 1.6mm)
        precip_mm = sum(precip_raw[:8]) * 1000.0 if any(0 < x < 0.1 for x in precip_raw[:8]) else sum(precip_raw[:8])
    else:
        precip_mm = float(precip_raw)

    wind_u = data.get("wind_u-surface", [0])
    wind_v = data.get("wind_v-surface", [0])
    max_wind_ms = 0.0
    if isinstance(wind_u, list) and isinstance(wind_v, list):
        for u, v in zip(wind_u[:8], wind_v[:8]):
            spd = (u**2 + v**2)**0.5
            if spd > max_wind_ms:
                max_wind_ms = spd
    elif isinstance(wind_u, (int, float)):
        max_wind_ms = abs(float(wind_u))

    temp_raw = data.get("temp-surface", [298.15])
    temp_k = temp_raw[0] if isinstance(temp_raw, list) and temp_raw else 298.15
    temp_c = temp_k - 273.15 if temp_k > 150 else temp_k

    event_lower = (event_type or "").lower()
    if "flood" in event_lower or "rain" in event_lower:
        hint = precip_mm > 5.0
    elif "wind" in event_lower or "storm" in event_lower or "cyclone" in event_lower:
        hint = max_wind_ms > 10.0  # > 36 km/h
    elif "heat" in event_lower:
        hint = temp_c > 38.0
    elif "fog" in event_lower:
        hint = temp_c < 16.0
    else:
        hint = precip_mm > 2.0

    set_cached_telemetry(hint_key, hint, ttl_seconds=1800)
    return hint

