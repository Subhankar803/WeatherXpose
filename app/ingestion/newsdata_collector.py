"""
NewsData.io collector — keyword search across NewsData's news index.
Uses standard HTTP requests to query the NewsData API for weather events in India.
"""
import requests
import logging
from datetime import datetime
from typing import List, Dict, Any

from app.config import settings
from app.ingestion.base_collector import BaseCollector
from app.utils.keywords import WEATHER_KEYWORDS

logger = logging.getLogger(__name__)

NEWSDATA_API_URL = "https://newsdata.io/api/1/news"


class NewsDataCollector(BaseCollector):
    name = "newsdata"

    def fetch(self) -> List[Dict[str, Any]]:
        if not settings.newsdata_api_key:
            return []

        events = []
        for keyword in WEATHER_KEYWORDS[:5]:  # Batch queries
            params = {
                "apikey": settings.newsdata_api_key,
                "q": f"India {keyword}",
                "country": "in",
                "language": "en",
            }
            try:
                r = requests.get(NEWSDATA_API_URL, params=params, timeout=8)
                if r.status_code == 200:
                    data = r.json()
                    for item in data.get("results", []):
                        events.append({
                            "source_platform": "newsdata",
                            "raw_text": f"{item.get('title', '')} — {item.get('description', '')}",
                            "timestamp": item.get("pubDate") or datetime.utcnow().isoformat(),
                            "city": None,
                            "state": None,
                            "latitude": None,
                            "longitude": None,
                            "media_urls": [item["image_url"]] if item.get("image_url") else [],
                            "event_type_guess": keyword,
                            "source_url": item.get("link"),
                            "source_name": item.get("source_name") or item.get("source_id", "NewsData.io"),
                        })
            except Exception as e:
                logger.warning(f"[newsdata_collector] query error: {e}")
                continue

        return events


def verify_news_for_location(city: str, event_type: str = "rainfall") -> bool:
    """
    Checks if recent GNews or NewsData reports corroborate a weather event in this location.
    Used by scoring.py (News verification check: +10 if Corroborated, +0 otherwise).
    """
    city_lower = (city or "").strip().lower()
    event_lower = (event_type or "").strip().lower()
    now = datetime.utcnow()

    # 1. Try GNews
    if settings.gnews_api_key and city_lower:
        try:
            url = "https://gnews.io/api/v4/search"
            params = {
                "q": f'"{city}" AND ({event_type} OR weather OR rain OR flood OR storm)',
                "lang": "en",
                "country": "in",
                "max": 5,
                "token": settings.gnews_api_key,
            }
            r = requests.get(url, params=params, timeout=6)
            if r.status_code == 200:
                articles = r.json().get("articles", [])
                for art in articles:
                    title = art.get("title", "").lower()
                    desc = art.get("description", "").lower()
                    combined = f"{title} {desc}"
                    if city_lower in combined and (event_lower in combined or any(w in combined for w in ["rain", "flood", "storm", "cyclone", "heat", "weather"])):
                        pub_str = art.get("publishedAt")
                        if pub_str:
                            try:
                                pub_dt = datetime.fromisoformat(pub_str.replace("Z", "+00:00").split("+")[0])
                                if (now - pub_dt).total_seconds() < 72 * 3600:
                                    logger.info(f"[news_verification] GNews matched: {art.get('title')}")
                                    return True
                            except Exception:
                                return True
                        else:
                            return True
        except Exception as e:
            logger.warning(f"[news_verification] GNews query note: {e}")

    # 2. Try NewsData
    if settings.newsdata_api_key and city_lower:
        try:
            params = {
                "apikey": settings.newsdata_api_key,
                "q": f"{city} {event_type}",
                "country": "in",
                "language": "en",
            }
            r = requests.get(NEWSDATA_API_URL, params=params, timeout=6)
            if r.status_code == 200:
                results = r.json().get("results", [])
                for item in results:
                    title = item.get("title", "").lower()
                    desc = item.get("description", "").lower()
                    combined = f"{title} {desc}"
                    if city_lower in combined:
                        pub_str = item.get("pubDate")
                        if pub_str:
                            try:
                                pub_dt = datetime.strptime(pub_str, "%Y-%m-%d %H:%M:%S")
                                if (now - pub_dt).total_seconds() < 72 * 3600:
                                    logger.info(f"[news_verification] NewsData matched: {item.get('title')}")
                                    return True
                            except Exception:
                                return True
                        else:
                            return True
        except Exception as e:
            logger.warning(f"[news_verification] NewsData query note: {e}")

    return False
