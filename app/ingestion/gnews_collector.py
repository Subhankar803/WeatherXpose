"""
GNews collector — keyword search across GNews's news index.
Every result is filtered through the shared WEATHER_KEYWORDS list
before being normalized and returned.
"""
import urllib.request
import urllib.parse
import json
from datetime import datetime

from app.config import settings
from app.ingestion.base_collector import BaseCollector
from app.utils.keywords import WEATHER_KEYWORDS

GNEWS_URL = "https://gnews.io/api/v4/search"


class GNewsCollector(BaseCollector):
    name = "gnews"

    def fetch(self) -> list[dict]:
        if not settings.gnews_api_key:
            print("[gnews_collector] GNEWS_API_KEY not set — skipping this run")
            return []

        events = []
        for keyword in WEATHER_KEYWORDS[:3]:
            params = {
                "q": f"India {keyword}",
                "lang": "en",
                "country": "in",
                "max": 5,
                "apikey": settings.gnews_api_key,
            }
            url = f"{GNEWS_URL}?{urllib.parse.urlencode(params)}"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "weather-platform-bot"})
                with urllib.request.urlopen(req, timeout=4) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except Exception as e:
                print(f"[gnews_collector] error fetching '{keyword}': {e}")
                continue

            for article in data.get("articles", []):
                events.append({
                    "source_platform": "gnews",
                    "raw_text": f"{article.get('title', '')} — {article.get('description', '')}",
                    "timestamp": article.get("publishedAt") or datetime.utcnow().isoformat(),
                    "city": None,
                    "state": None,
                    "latitude": None,
                    "longitude": None,
                    "media_urls": [article["image"]] if article.get("image") else [],
                    "event_type_guess": keyword,
                    "source_url": article.get("url"),
                    "source_name": article.get("source", {}).get("name"),
                })
        return events
