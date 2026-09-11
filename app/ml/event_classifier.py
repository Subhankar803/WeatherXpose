"""
Event categorization module.
Classifies text into: rainfall, flooding, thunderstorm, heatwave, fog, dust_storm, cyclone, hailstorm, strong_winds.
"""
from app.ml.trained_model import predict_event_category


def classify_event(raw_text: str) -> str:
    """Returns one event category string for the given raw text."""
    if not raw_text:
        return "general_weather"
    return predict_event_category(raw_text)
