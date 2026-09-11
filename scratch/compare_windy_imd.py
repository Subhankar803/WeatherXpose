import sys
sys.path.insert(0, ".")

from app.ingestion.imd_collector import IMDCollector
from app.ingestion.windy_collector import check_windy_strong_hint
from app.ingestion.openweather_collector import get_city_current_weather

imd = IMDCollector()
cities = [
    ('Mumbai', 'Maharashtra', 19.076, 72.877, 'Rain'),
    ('Kolkata', 'West Bengal', 22.5726, 88.3639, 'Rain'),
    ('Delhi', 'Delhi', 28.6139, 77.209, 'Rain'),
    ('Bangalore', 'Karnataka', 12.9716, 77.5946, 'Rain'),
    ('Chennai', 'Tamil Nadu', 13.0827, 80.2707, 'Rain'),
    ('Pune', 'Maharashtra', 18.5204, 73.8567, 'Rain'),
]

for city, state, lat, lon, ev in cities:
    windy_res = check_windy_strong_hint(lat, lon, ev)
    imd_warn = imd.get_district_warning(city, state)
    ow_res = get_city_current_weather(city)
    print(f"[{city}, {state}]")
    print(f"  Windy: {windy_res}")
    print(f"  IMD has_warning: {imd_warn.get('has_warning')} | severity: {imd_warn.get('severity')} | type: {imd_warn.get('warning_type')} | text: {imd_warn.get('text', '')[:80]}")
    print(f"  OpenWeather: {ow_res.get('condition')} | precip: {ow_res.get('precipitation_mm')}mm | temp: {ow_res.get('temperature')}C")
    print("-" * 60)
