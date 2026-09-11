"""
Ingestion Collectors Integration Tests.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ingestion.imd_collector import IMDCollector
from app.ingestion.windy_collector import WindyCollector, check_windy_strong_hint
from app.ingestion.newsdata_collector import NewsDataCollector, verify_news_for_location
from app.ingestion.openweather_collector import get_city_current_weather


def test_imd_collector_fetch():
    """Verify IMD collector returns structured bulletins."""
    col = IMDCollector()
    events = col.fetch()
    assert isinstance(events, list)
    assert len(events) > 0
    first = events[0]
    assert first["source_platform"] == "imd"
    assert "raw_text" in first
    assert "city" in first


def test_imd_district_warning():
    """Verify IMD district warning lookup helper."""
    col = IMDCollector()
    warning = col.get_district_warning("Mumbai")
    assert isinstance(warning, dict)
    assert "has_warning" in warning


def test_openweather_telemetry():
    """Verify OpenWeather real-time telemetry."""
    weather = get_city_current_weather("Delhi")
    assert isinstance(weather, dict)
    assert weather["city"] == "Delhi"
    assert "temperature" in weather
    assert "humidity" in weather
    assert "wind_speed_kmh" in weather


def test_news_verification_helper():
    """Verify news corroboration function."""
    res = verify_news_for_location("Mumbai", "rainfall")
    assert isinstance(res, bool)


def test_windy_hint_helper():
    """Verify Windy atmospheric plausibility helper."""
    hint = check_windy_strong_hint(19.0760, 72.8777, "rainfall")
    assert isinstance(hint, bool)


if __name__ == "__main__":
    print("Running ingestion tests...")
    test_imd_collector_fetch()
    print("[PASS] test_imd_collector_fetch")
    test_imd_district_warning()
    print("[PASS] test_imd_district_warning")
    test_openweather_telemetry()
    print("[PASS] test_openweather_telemetry")
    test_news_verification_helper()
    print("[PASS] test_news_verification_helper")
    test_windy_hint_helper()
    print("[PASS] test_windy_hint_helper")
    print("\nALL INGESTION TESTS PASSED SUCCESSFULLY!")
