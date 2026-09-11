"""
Machine Learning Model Pipeline & Inference Engine.

Integrates:
1. text_classifier.pkl + tfidf_vectorizer.pkl -> Disaster Alert Text Classification (True/False)
2. weather_classifier.pkl -> Meteorological Pattern Classification
3. flood_regressor.pkl -> Flood Risk Probability Regressor
4. event_classifier.joblib -> Multi-class Weather Event Categorizer
"""
import os
import logging
from datetime import datetime
from typing import Any, Optional, Dict, List, Tuple
import pandas as pd

try:
    import joblib
except ImportError:
    import pickle as joblib

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

# Feature schemas
WEATHER_FEATURE_NAMES = [
    "temperature_2m_max", "temperature_2m_min", "apparent_temperature_max",
    "apparent_temperature_min", "precipitation_sum", "rain_sum",
    "wind_speed_10m_max", "wind_gusts_10m_max", "wind_direction_10m_dominant",
    "month", "day_of_year", "temp_range", "apparent_temp_range",
]

FLOOD_FEATURE_NAMES = [
    "MonsoonIntensity", "TopographyDrainage", "RiverManagement", "Deforestation",
    "Urbanization", "ClimateChange", "DamsQuality", "Siltation", "AgriculturalPractices",
    "Encroachments", "IneffectiveDisasterPreparedness", "DrainageSystems",
    "CoastalVulnerability", "Landslides", "Watersheds", "DeterioratingInfrastructure",
    "PopulationScore", "WetlandLoss", "InadequatePlanning", "PoliticalFactors",
]

# Major Indian cities reference coordinates
CITY_COORDS: Dict[str, Tuple[float, float]] = {
    "Delhi": (28.6139, 77.2090), "New Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777), "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639), "Bangalore": (12.9716, 77.5946),
    "Bengaluru": (12.9716, 77.5946), "Hyderabad": (17.3850, 78.4867),
    "Ahmedabad": (23.0225, 72.5714), "Pune": (18.5204, 73.8567),
    "Jaipur": (26.9124, 75.7873), "Lucknow": (26.8467, 80.9462),
    "Patna": (25.5941, 85.1376), "Guwahati": (26.1445, 91.7362),
    "Bhopal": (23.2599, 77.4126), "Thiruvananthapuram": (8.5241, 76.9366),
    "Chandigarh": (30.7333, 76.7794), "Surat": (21.1702, 72.8311),
    "Nagpur": (21.1458, 79.0882), "Visakhapatnam": (17.6868, 83.2185),
    "Kochi": (9.9312, 76.2673), "Bhubaneswar": (20.2961, 85.8245),
    "Dehradun": (30.3165, 78.0322), "Shimla": (31.1048, 77.1734),
    "Srinagar": (34.0837, 74.7973), "Ranchi": (23.3441, 85.3096),
}

CITY_FLOOD_PROFILE: Dict[str, List[float]] = {
    "Delhi":     [5, 8, 5, 5, 7, 7, 17, 5, 5, 5, 5, 11, 2, 5, 5, 19, 8, 5, 5, 1],
    "Mumbai":    [5, 9, 6, 4, 9, 8, 12, 6, 2, 8, 6, 15, 9, 3, 6, 14, 9, 7, 7, 2],
    "Chennai":   [5, 7, 5, 3, 8, 7, 10, 5, 3, 7, 5, 12, 8, 2, 5, 12, 8, 6, 6, 2],
    "Kolkata":   [5, 6, 4, 4, 8, 8, 11, 7, 4, 8, 6, 14, 7, 2, 6, 15, 8, 8, 6, 2],
    "Bengaluru": [5, 8, 5, 3, 9, 6, 8, 4, 3, 7, 4, 10, 1, 4, 5, 11, 8, 5, 5, 1],
    "Hyderabad": [5, 7, 5, 4, 8, 7, 10, 5, 4, 7, 5, 11, 1, 3, 5, 12, 8, 5, 5, 1],
    "Patna":     [5, 8, 7, 5, 7, 8, 13, 8, 5, 7, 7, 13, 1, 2, 7, 16, 8, 7, 6, 2],
    "Guwahati":  [5, 9, 8, 6, 7, 8, 14, 9, 6, 7, 7, 13, 2, 6, 8, 15, 7, 8, 6, 2],
}

_text_clf = None
_tfidf_vec = None
_weather_clf = None
_flood_reg = None
_event_clf = None
_models_loaded = False


def load_all_models():
    """Loads all trained models once at startup or on first call."""
    global _text_clf, _tfidf_vec, _weather_clf, _flood_reg, _event_clf, _models_loaded
    if _models_loaded:
        return

    def _safe_load(filename):
        p = os.path.join(MODELS_DIR, filename)
        if os.path.exists(p):
            try:
                return joblib.load(p)
            except Exception as e:
                logger.warning(f"Could not load {filename}: {e}")
        return None

    _text_clf = _safe_load("text_classifier.pkl")
    _tfidf_vec = _safe_load("tfidf_vectorizer.pkl")
    _weather_clf = _safe_load("weather_classifier.pkl")
    _flood_reg = _safe_load("flood_regressor.pkl")
    _event_clf = _safe_load("event_classifier.joblib")

    _models_loaded = True
    logger.info("All available ML models initialized.")


def get_flood_profile(city: str) -> List[float]:
    if city in CITY_FLOOD_PROFILE:
        return list(CITY_FLOOD_PROFILE[city])
    return [5.0] * 20


def map_precip_to_monsoon_intensity(precip_mm: float) -> float:
    if precip_mm <= 0:
        return 2.0
    elif precip_mm < 2.5:
        return 5.0
    elif precip_mm < 7.5:
        return 9.0
    elif precip_mm < 35.5:
        return 14.0
    elif precip_mm < 64.5:
        return 18.0
    return 20.0


def predict_disaster_text(raw_text: str) -> bool:
    """Predicts whether the text discusses an active disaster / emergency."""
    load_all_models()
    if _text_clf is None or _tfidf_vec is None:
        # Fallback keywords
        lower = raw_text.lower()
        keywords = ["flood", "heavy rain", "storm", "cyclone", "heatwave", "landslide", "drown", "waterlog", "imd"]
        return any(k in lower for k in keywords)

    try:
        vec = _tfidf_vec.transform([raw_text])
        pred = _text_clf.predict(vec)[0]
        return bool(pred)
    except Exception as e:
        logger.error(f"Error in text classification: {e}")
        return False


def predict_weather_code(weather_features: List[float]) -> int:
    """Predicts meteorological condition classification code."""
    load_all_models()
    if _weather_clf is None or len(weather_features) != len(WEATHER_FEATURE_NAMES):
        return 1  # Standard weather code
    try:
        df = pd.DataFrame([weather_features], columns=WEATHER_FEATURE_NAMES)
        pred = _weather_clf.predict(df)[0]
        return int(pred)
    except Exception as e:
        logger.error(f"Error in weather code prediction: {e}")
        return 1


def predict_flood_risk(flood_features: List[float]) -> float:
    """Predicts flood probability risk score (0.0 to 1.0)."""
    load_all_models()
    if _flood_reg is None or len(flood_features) != len(FLOOD_FEATURE_NAMES):
        intensity = flood_features[0] if flood_features else 5.0
        return min(1.0, max(0.0, intensity / 25.0))
    try:
        df = pd.DataFrame([flood_features], columns=FLOOD_FEATURE_NAMES)
        score = _flood_reg.predict(df)[0]
        return round(float(score), 4)
    except Exception as e:
        logger.error(f"Error in flood regression: {e}")
        return 0.35


def predict_event_category(raw_text: str) -> str:
    """Predicts the event category name (earthquake, rainfall, flooding, thunderstorm, etc.)."""
    lower = (raw_text or "").lower()
    # High-priority disaster and geophysical keyword check
    if any(k in lower for k in ["earthquake", "earth quack", "quake", "tremor", "seismic", "richter"]):
        return "earthquake"
    if any(k in lower for k in ["tsunami", "tidal wave"]):
        return "tsunami"
    if any(k in lower for k in ["landslide", "mudslide", "rockslide"]):
        return "landslide"

    load_all_models()
    if _event_clf is not None:
        try:
            res = _event_clf.predict([raw_text])[0] if hasattr(_event_clf, "predict") else None
            if res:
                return str(res)
        except Exception:
            pass

    # Keyword fallback
    if any(k in lower for k in ["flood", "waterlogging", "submerged"]):
        return "flooding"
    if any(k in lower for k in ["thunderstorm", "lightning"]):
        return "thunderstorm"
    if any(k in lower for k in ["heavy rain", "rainfall", "downpour", "monsoon"]):
        return "rainfall"
    if any(k in lower for k in ["heatwave", "extreme heat", "loo"]):
        return "heatwave"
    if any(k in lower for k in ["fog", "smog", "visibility"]):
        return "fog"
    if any(k in lower for k in ["cyclone", "typhoon", "hurricane"]):
        return "cyclone"
    if any(k in lower for k in ["dust storm", "andhi"]):
        return "dust_storm"
    if any(k in lower for k in ["hailstorm", "hail"]):
        return "hailstorm"
    if any(k in lower for k in ["strong wind", "gale", "gust"]):
        return "strong_winds"
    return "general_weather"


def evaluate_city_fusion(
    city: str,
    raw_text: str = "",
    temp_c: float = 28.0,
    precip_mm: float = 0.0,
    wind_kmh: float = 15.0,
) -> Dict[str, Any]:
    """Runs data fusion evaluation across all trained models for a city."""
    now = datetime.now()
    if not raw_text:
        raw_text = f"Weather update for {city} with temperature {temp_c}C and precipitation {precip_mm}mm."

    is_disaster = predict_disaster_text(raw_text)
    event_category = predict_event_category(raw_text)

    weather_features = [
        round(temp_c + 2.0, 1), round(temp_c - 2.0, 1), round(temp_c + 1.0, 1), round(temp_c - 3.0, 1),
        round(precip_mm, 2), round(precip_mm, 2),
        round(wind_kmh, 1), round(wind_kmh * 1.3, 1), 180,
        now.month, now.timetuple().tm_yday,
        4.0, 0.0,
    ]
    weather_code = predict_weather_code(weather_features)

    flood_features = get_flood_profile(city)
    flood_features[0] = map_precip_to_monsoon_intensity(precip_mm)
    flood_risk = predict_flood_risk(flood_features)

    lat, lon = CITY_COORDS.get(city, (20.5937, 78.9629))

    return {
        "city": city,
        "latitude": lat,
        "longitude": lon,
        "is_disaster_alert": is_disaster,
        "event_category": event_category,
        "predicted_weather_code": weather_code,
        "flood_probability_score": flood_risk,
        "measured_precipitation_mm": precip_mm,
        "monsoon_intensity_level": flood_features[0],
    }
