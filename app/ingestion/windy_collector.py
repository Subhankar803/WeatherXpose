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

    point_key = settings.windy_point_key or settings.windy_api_key
    if not point_key:
        return None  # key not set yet — fail safe, don't crash ingestion

    payload = {
        "lat": lat,
        "lon": lon,
        "model": model,
        "parameters": ["temp", "wind", "rh", "pressure", "precip"],
        "levels": ["surface"],
        "key": point_key,
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
    webcam_key = settings.windy_webcam_key or settings.windy_api_key
    if not webcam_key:
        return []

    headers = {"x-windy-api-key": webcam_key}
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


def evaluate_windy_telemetry(lat: float, lon: float, event_type: str = "rainfall", incident_time: object = None) -> dict:
    """
    Evaluates Windy point forecast numerical model data dynamically across situations.
    Scores range from minimum 5 pts (calm / dry baseline) up to maximum 15 pts (severe weather).
    Returns an authentic telemetry hint with exact numbers (precip_mm, wind gusts, temp, rh).
    Caches evaluation for 30 minutes to guarantee deterministic scoring.
    """
    date_str = ""
    parsed_dt = None
    target_ms = None
    if incident_time:
        try:
            from app.services.image_forensics import parse_datetime_flexible
            parsed_dt = incident_time if hasattr(incident_time, "timestamp") else parse_datetime_flexible(str(incident_time))
            if parsed_dt:
                date_str = parsed_dt.strftime("%Y-%m-%d")
                target_ms = int(parsed_dt.timestamp() * 1000)
            else:
                date_str = str(incident_time)[:10]
        except Exception:
            date_str = str(incident_time)[:10]

    cache_key = f"windy_eval:{round(lat, 2)}_{round(lon, 2)}_{(event_type or '').lower()}"
    if date_str:
        cache_key += f"_{date_str}"
    cached_eval = get_cached_telemetry(cache_key)
    if cached_eval is not None and isinstance(cached_eval, dict):
        return cached_eval

    forecast = get_point_forecast(lat, lon)
    if not forecast:
        res = {
            "points": 5,
            "passed": False,
            "status": "Windy telemetry model data currently unavailable (Minimum baseline: +5 pts)",
            "windy_hint": "Windy Model: Telemetry currently unavailable; baseline applied (5 pts)",
            "precip_mm": 0.0,
            "max_wind_kmh": 0.0,
            "temp_c": 25.0,
            "rh": 50.0,
            "is_historical_outside_window": False,
        }
        set_cached_telemetry(cache_key, res, ttl_seconds=1800)
        return res

    data = forecast.get("data", forecast)
    precip_raw = data.get("past3hprecip-surface") or data.get("precip-surface") or [0]
    wind_u = data.get("wind_u-surface", [0])
    wind_v = data.get("wind_v-surface", [0])
    temp_raw = data.get("temp-surface", [298.15])
    rh_raw = data.get("rh-surface", [60.0])
    ts = data.get("ts", [])

    is_historical_outside_window = False
    slice_start = 0
    slice_end = 8
    if target_ms is not None and ts and len(ts) > 0:
        min_ts = ts[0] - 86400000
        max_ts = ts[-1] + 86400000
        if target_ms < min_ts or target_ms > max_ts:
            is_historical_outside_window = True
        else:
            closest_idx = min(range(len(ts)), key=lambda i: abs(ts[i] - target_ms))
            slice_start = max(0, closest_idx - 3)
            slice_end = min(len(ts), closest_idx + 4)

    if is_historical_outside_window:
        res = {
            "points": 5,
            "passed": False,
            "status": f"Windy Model: Date {date_str} is outside 10-day active forecast window; no active model anomaly",
            "windy_hint": f"Windy Model: Date {date_str} outside 10-day active forecast window; baseline applied (+5 pts)",
            "precip_mm": 0.0,
            "max_wind_kmh": 0.0,
            "temp_c": 25.0,
            "rh": 60.0,
            "is_historical_outside_window": True,
        }
        set_cached_telemetry(cache_key, res, ttl_seconds=1800)
        return res

    # Calculate precipitation in mm
    if isinstance(precip_raw, list):
        target_slice = precip_raw[slice_start:slice_end] if len(precip_raw) >= slice_end else precip_raw
        if any(0.0 < float(x) < 0.5 for x in target_slice):
            precip_mm = round(max(0.0, sum(float(x) for x in target_slice) * 1000.0), 1)
        else:
            precip_mm = round(max(0.0, sum(float(x) for x in target_slice)), 1)
    else:
        precip_mm = round(float(precip_raw), 1)

    # Calculate max wind speed in km/h
    max_wind_ms = 0.0
    if isinstance(wind_u, list) and isinstance(wind_v, list):
        u_slice = wind_u[slice_start:slice_end] if len(wind_u) >= slice_end else wind_u
        v_slice = wind_v[slice_start:slice_end] if len(wind_v) >= slice_end else wind_v
        for u, v in zip(u_slice, v_slice):
            spd = (float(u)**2 + float(v)**2)**0.5
            if spd > max_wind_ms:
                max_wind_ms = spd
    elif isinstance(wind_u, (int, float)):
        max_wind_ms = abs(float(wind_u))
    max_wind_kmh = round(max_wind_ms * 3.6, 1)

    # Temperature in Celsius
    t_slice = temp_raw[slice_start:slice_end] if isinstance(temp_raw, list) else [temp_raw]
    mean_k = sum(float(x) for x in t_slice) / max(1, len(t_slice))
    temp_c = round(mean_k - 273.15 if mean_k > 150 else mean_k, 1)

    # Relative humidity in %
    r_slice = rh_raw[slice_start:slice_end] if isinstance(rh_raw, list) else [rh_raw]
    rh = round(sum(float(x) for x in r_slice) / max(1, len(r_slice)), 1)

    event_lower = (event_type or "").lower()
    points = 5
    verdict = "Calm / dry conditions"

    # Situation-based scoring logic (5 to 15 points)
    if any(k in event_lower for k in ["flood", "waterlog", "rain", "shower", "cloudburst", "drizzle"]):
        if precip_mm >= 25.0 or (precip_mm >= 15.0 and max_wind_kmh >= 35.0):
            points = 15
            verdict = "Heavy torrential rainfall corroborated by Windy model"
        elif precip_mm >= 12.0 or (precip_mm >= 7.0 and max_wind_kmh >= 30.0):
            points = 13
            verdict = "Significant precipitation corroborated by Windy model"
        elif precip_mm >= 6.0 or (precip_mm >= 3.0 and max_wind_kmh >= 25.0):
            points = 10
            verdict = "Moderate rainfall signal detected on Windy model"
        elif precip_mm >= 1.5 or max_wind_kmh >= 20.0:
            points = 8
            verdict = "Light / trace rainfall detected on Windy model"
        elif precip_mm >= 0.5:
            points = 6
            verdict = "Marginal trace precipitation on Windy model"
        else:
            points = 5
            verdict = "Dry / calm conditions on Windy model (no rain signal)"

    elif any(k in event_lower for k in ["cyclone", "storm", "wind", "gale", "squall", "thunder"]):
        if max_wind_kmh >= 60.0 or (max_wind_kmh >= 45.0 and precip_mm >= 12.0):
            points = 15
            verdict = "Severe cyclonic gale / storm gusts corroborated by Windy model"
        elif max_wind_kmh >= 45.0 or (max_wind_kmh >= 35.0 and precip_mm >= 6.0):
            points = 13
            verdict = "Strong squall / high wind conditions corroborated by Windy model"
        elif max_wind_kmh >= 30.0 or precip_mm >= 4.0:
            points = 10
            verdict = "Moderate gusty winds / thunderstorm activity on Windy model"
        elif max_wind_kmh >= 20.0:
            points = 7
            verdict = "Breezy conditions detected on Windy model"
        else:
            points = 5
            verdict = "Calm to gentle breeze on Windy model"

    elif "heat" in event_lower:
        if temp_c >= 42.0:
            points = 15
            verdict = "Extreme heatwave temperatures corroborated by Windy model"
        elif temp_c >= 39.0:
            points = 12
            verdict = "High heatwave temperatures corroborated by Windy model"
        elif temp_c >= 36.0:
            points = 8
            verdict = "Elevated temperature signal on Windy model"
        else:
            points = 5
            verdict = "Normal temperature range on Windy model"

    elif any(k in event_lower for k in ["fog", "cold", "mist", "frost"]):
        if temp_c <= 8.0 and rh >= 80.0:
            points = 15
            verdict = "Dense fog / severe cold wave corroborated by Windy model"
        elif temp_c <= 13.0 and rh >= 70.0:
            points = 11
            verdict = "Moderate fog / cool conditions on Windy model"
        elif temp_c <= 17.0:
            points = 7
            verdict = "Mild cool / mist signal on Windy model"
        else:
            points = 5
            verdict = "Normal conditions on Windy model"

    else:
        # Generic hazard: evaluate combined precipitation and wind scale
        if precip_mm >= 20.0 or max_wind_kmh >= 55.0:
            points = 15
            verdict = "Severe weather conditions corroborated by Windy model"
        elif precip_mm >= 10.0 or max_wind_kmh >= 38.0:
            points = 12
            verdict = "Moderate to strong atmospheric signals on Windy model"
        elif precip_mm >= 4.0 or max_wind_kmh >= 25.0:
            points = 9
            verdict = "Moderate atmospheric signals on Windy model"
        elif precip_mm >= 1.0 or max_wind_kmh >= 18.0:
            points = 7
            verdict = "Light atmospheric signals on Windy model"
        else:
            points = 5
            verdict = "Calm atmospheric baseline on Windy model"

    points = max(5, min(15, points))
    passed = points > 5
    windy_hint_str = f"Windy Model Telemetry: {precip_mm}mm rain, {max_wind_kmh} km/h wind, {temp_c}°C, {rh}% RH — {verdict} (+{points} pts)"

    res = {
        "points": points,
        "passed": passed,
        "status": f"{verdict} ({precip_mm}mm rain, {max_wind_kmh} km/h wind, {temp_c}°C)",
        "windy_hint": windy_hint_str,
        "precip_mm": precip_mm,
        "max_wind_kmh": max_wind_kmh,
        "temp_c": temp_c,
        "rh": rh,
        "is_historical_outside_window": False,
    }
    set_cached_telemetry(cache_key, res, ttl_seconds=1800)
    return res


def check_windy_strong_hint(lat: float, lon: float, event_type: str = "rainfall", incident_time: object = None) -> bool:
    """
    Evaluates whether Windy point forecast provides a strong hint for the claimed weather incident.
    Backward-compatible wrapper around evaluate_windy_telemetry.
    """
    eval_res = evaluate_windy_telemetry(lat, lon, event_type, incident_time=incident_time)
    return bool(eval_res.get("passed", False))

