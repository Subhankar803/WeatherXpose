"""
Shared WEATHER_KEYWORDS list used by every ingestion collector to filter
raw content down to weather-relevant posts. Single source of truth —
update this list here, not inside individual collectors.
"""
WEATHER_KEYWORDS = [
    "IMD", "flood", "flooding", "heavy rainfall", "waterlogging",
    "thunderstorm", "heatwave", "dust storm", "fog alert",
    "cyclone", "strong winds", "hailstorm", "lightning strike",
]
