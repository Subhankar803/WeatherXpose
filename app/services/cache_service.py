"""
Two-Tier Persistent Disk & Redis Caching Engine for Weather & Verification.

Features:
- Tier 1: Real-time Location Weather Grid (temperature, rainfall, wind, pressure, IMD alerts)
          Refreshed on a 10-minute cycle (TTL = 600s).
- Tier 2: Highlighted Weather Incidents (Floods, Cyclones, Heatwaves, etc.)
          Stored per location with text description, rainfall, temp, and timeline.
          Retained for exactly 7 days (TTL = 604,800s / 7 days).
- Incident Verification Cache: Fast O(1) deduplication and incident retrieval.
- Telemetry Cache: Stable caching for Windy point forecasts, OpenWeather station reports,
  and IMD bulletins so scores remain deterministic and API rate limits are preserved.
- Automatic Disk-File Persistence: Saves to cache/*.json on disk so cache survives server reloads.
- Redis support: Transparently uses Redis if online, with instantaneous in-memory + file fallback.
"""
import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from app.cache import redis_client

logger = logging.getLogger(__name__)

# Persistent File Cache Directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
try:
    os.makedirs(CACHE_DIR, exist_ok=True)
except Exception as _e:
    logger.warning(f"Could not create cache dir {CACHE_DIR}: {_e}")

TELEMETRY_CACHE_FILE = os.path.join(CACHE_DIR, "telemetry_cache.json")
INCIDENT_CACHE_FILE = os.path.join(CACHE_DIR, "incident_cache.json")
EVENTS_7DAY_CACHE_FILE = os.path.join(CACHE_DIR, "7day_events_cache.json")
TIER1_WEATHER_CACHE_FILE = os.path.join(CACHE_DIR, "weather_grid_cache.json")


def _load_json_file(filepath: str) -> Dict[str, Any]:
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        except Exception as e:
            logger.warning(f"Error loading cache file {filepath}: {e}")
    return {}


def _save_json_file(filepath: str, data: Any):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Error persisting cache file {filepath}: {e}")


# In-memory fast tier initialized from disk files
_mem_tier1_weather: Dict[str, Dict[str, Any]] = _load_json_file(TIER1_WEATHER_CACHE_FILE)
_mem_tier2_events: Dict[str, List[Dict[str, Any]]] = _load_json_file(EVENTS_7DAY_CACHE_FILE)
_mem_incident_cache: Dict[str, Dict[str, Any]] = _load_json_file(INCIDENT_CACHE_FILE)
_mem_telemetry_cache: Dict[str, Dict[str, Any]] = _load_json_file(TELEMETRY_CACHE_FILE)

SEVEN_DAYS_SECONDS = 7 * 24 * 3600
TEN_MINUTES_SECONDS = 10 * 60

_redis_status = None
_redis_last_check = 0.0


def _redis_available() -> bool:
    global _redis_status, _redis_last_check
    now = time.time()
    if _redis_status is not None and (now - _redis_last_check) < 120.0:
        return _redis_status
    _redis_last_check = now
    try:
        redis_client.ping()
        _redis_status = True
    except Exception:
        _redis_status = False
    return _redis_status


# ─────────────────────────────────────────────────────────────
# TELEMETRY CACHE (Windy, OpenWeather, IMD Bulletins, Atmospheric)
# ─────────────────────────────────────────────────────────────

def set_cached_telemetry(key: str, data: Any, ttl_seconds: int = 1800):
    """
    Caches external API telemetry (Windy, OpenWeather, IMD, News) both in memory
    and on persistent disk to prevent continuous external API hammering and score jitter.
    """
    clean_key = str(key).strip().lower()
    entry = {
        "data": data,
        "expires_at": time.time() + ttl_seconds,
        "cached_at": datetime.utcnow().isoformat(),
    }
    _mem_telemetry_cache[clean_key] = entry
    _save_json_file(TELEMETRY_CACHE_FILE, _mem_telemetry_cache)


def get_cached_telemetry(key: str) -> Optional[Any]:
    """Retrieves cached telemetry if not expired."""
    clean_key = str(key).strip().lower()
    entry = _mem_telemetry_cache.get(clean_key)
    if entry and isinstance(entry, dict):
        if time.time() < entry.get("expires_at", 0):
            return entry.get("data")
        else:
            del _mem_telemetry_cache[clean_key]
            _save_json_file(TELEMETRY_CACHE_FILE, _mem_telemetry_cache)
    return None


# ─────────────────────────────────────────────────────────────
# TIER 1: Real-time Location Weather Grid (5-10 min TTL)
# ─────────────────────────────────────────────────────────────

def set_location_weather(city: str, weather_data: Dict[str, Any], ttl_seconds: int = TEN_MINUTES_SECONDS):
    """Sets live weather telemetry for a location in memory, disk file, and Redis."""
    city_clean = city.lower().strip()
    key = f"weather:grid:{city_clean}"
    weather_data["cached_at"] = datetime.utcnow().isoformat()
    weather_data["expires_in_sec"] = ttl_seconds

    if _redis_available():
        try:
            redis_client.setex(key, ttl_seconds, json.dumps(weather_data))
        except Exception as e:
            logger.warning(f"Redis write error: {e}")

    # Memory + Disk File
    _mem_tier1_weather[city_clean] = {
        "data": weather_data,
        "expires_at": time.time() + ttl_seconds
    }
    _save_json_file(TIER1_WEATHER_CACHE_FILE, _mem_tier1_weather)


def get_location_weather(city: str) -> Optional[Dict[str, Any]]:
    """Retrieves live weather telemetry for a location from cache."""
    city_clean = city.lower().strip()
    key = f"weather:grid:{city_clean}"
    if _redis_available():
        try:
            raw = redis_client.get(key)
            if raw:
                return json.loads(raw)
        except Exception as e:
            logger.warning(f"Redis read error: {e}")

    # Check memory / file cache
    entry = _mem_tier1_weather.get(city_clean)
    if entry and isinstance(entry, dict):
        if time.time() < entry.get("expires_at", 0):
            return entry.get("data")
        else:
            del _mem_tier1_weather[city_clean]
            _save_json_file(TIER1_WEATHER_CACHE_FILE, _mem_tier1_weather)
    return None


def get_all_cached_weather_grid() -> List[Dict[str, Any]]:
    """Returns all active location weather rows."""
    results = []
    if _redis_available():
        try:
            keys = redis_client.keys("weather:grid:*")
            for k in keys:
                raw = redis_client.get(k)
                if raw:
                    results.append(json.loads(raw))
            if results:
                return results
        except Exception as e:
            logger.warning(f"Redis keys error: {e}")

    now = time.time()
    for city, entry in list(_mem_tier1_weather.items()):
        if isinstance(entry, dict) and now < entry.get("expires_at", 0):
            results.append(entry["data"])
        else:
            _mem_tier1_weather.pop(city, None)
    return results


# ─────────────────────────────────────────────────────────────
# TIER 2: Highlighted Weather Incidents (7-Day TTL per event)
# ─────────────────────────────────────────────────────────────

def add_highlighted_event(city: str, event_data: Dict[str, Any]):
    """
    Adds a highlighted severe weather event for a city (e.g. Flood, Cyclone).
    Each event has its own 7-day expiration from the time it is added/updated.
    """
    city_key = city.lower().strip()
    event_id = event_data.get("id") or f"{city_key}_{int(time.time())}"
    event_data["id"] = event_id
    event_data["city"] = city
    event_data["created_at"] = event_data.get("created_at") or datetime.utcnow().isoformat()
    event_data["expires_at_timestamp"] = time.time() + SEVEN_DAYS_SECONDS

    key = f"weather:events:7day:{city_key}:{event_id}"

    if _redis_available():
        try:
            redis_client.setex(key, SEVEN_DAYS_SECONDS, json.dumps(event_data))
            redis_client.sadd(f"weather:locations:active_events:{city_key}", event_id)
        except Exception as e:
            logger.warning(f"Redis event add error: {e}")

    # Fallback in-memory + file
    if city_key not in _mem_tier2_events or not isinstance(_mem_tier2_events[city_key], list):
        _mem_tier2_events[city_key] = []
    _mem_tier2_events[city_key].append(event_data)
    _save_json_file(EVENTS_7DAY_CACHE_FILE, _mem_tier2_events)


def get_city_active_7day_events(city: str) -> List[Dict[str, Any]]:
    """Returns active highlighted events for a city within the 7-day window."""
    city_key = city.lower().strip()
    events = []

    if _redis_available():
        try:
            keys = redis_client.keys(f"weather:events:7day:{city_key}:*")
            for k in keys:
                raw = redis_client.get(k)
                if raw:
                    events.append(json.loads(raw))
            if events:
                return events
        except Exception as e:
            logger.warning(f"Redis get events error: {e}")

    now = time.time()
    active = []
    for ev in _mem_tier2_events.get(city_key, []):
        if isinstance(ev, dict) and ev.get("expires_at_timestamp", 0) > now:
            active.append(ev)
    _mem_tier2_events[city_key] = active
    return active


def get_all_active_7day_events() -> List[Dict[str, Any]]:
    """Returns all highlighted weather incidents across India within 7-day window."""
    events = []
    if _redis_available():
        try:
            keys = redis_client.keys("weather:events:7day:*")
            for k in keys:
                raw = redis_client.get(k)
                if raw:
                    events.append(json.loads(raw))
            if events:
                return events
        except Exception as e:
            logger.warning(f"Redis all events error: {e}")

    now = time.time()
    for city_key, ev_list in list(_mem_tier2_events.items()):
        if isinstance(ev_list, list):
            active = [ev for ev in ev_list if isinstance(ev, dict) and ev.get("expires_at_timestamp", 0) > now]
            _mem_tier2_events[city_key] = active
            events.extend(active)
    return events


# ─────────────────────────────────────────────────────────────
# INCIDENT / RESEARCH VERIFICATION CACHE (Fast lookup)
# ─────────────────────────────────────────────────────────────

def cache_incident_result(cache_key: str, incident_data: Dict[str, Any], ttl_seconds: int = 86400):
    """Caches researched incident verification result to memory, disk file, and Redis."""
    clean_key = str(cache_key).strip().lower()
    key = f"incident:result:{clean_key}"
    if _redis_available():
        try:
            redis_client.setex(key, ttl_seconds, json.dumps(incident_data))
        except Exception:
            pass

    _mem_incident_cache[clean_key] = {
        "data": incident_data,
        "expires_at": time.time() + ttl_seconds,
        "cached_at": datetime.utcnow().isoformat(),
    }
    _save_json_file(INCIDENT_CACHE_FILE, _mem_incident_cache)


def get_cached_incident_result(cache_key: str) -> Optional[Dict[str, Any]]:
    """Checks if an incident has already been verified and cached."""
    clean_key = str(cache_key).strip().lower()
    key = f"incident:result:{clean_key}"
    if _redis_available():
        try:
            raw = redis_client.get(key)
            if raw:
                return json.loads(raw)
        except Exception:
            pass

    entry = _mem_incident_cache.get(clean_key)
    if entry and isinstance(entry, dict):
        if time.time() < entry.get("expires_at", 0):
            return entry.get("data")
        else:
            del _mem_incident_cache[clean_key]
            _save_json_file(INCIDENT_CACHE_FILE, _mem_incident_cache)
    return None
