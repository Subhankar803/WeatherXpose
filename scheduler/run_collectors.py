import os
import sys
import time
import logging
from datetime import datetime

# Ensure parent root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database_setup import SessionLocal
from app.ingestion.imd_collector import IMDCollector
from app.ingestion.gnews_collector import GNewsCollector
from app.ingestion.newsdata_collector import NewsDataCollector
from app.ingestion.openweather_collector import get_city_current_weather
from app.services.cache_service import set_location_weather
from app.services.verification_engine import process_and_verify_incident

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("scheduler")

MAJOR_INDIAN_METROS = [
    "Mumbai", "Delhi", "Kolkata", "Chennai", "Bengaluru",
    "Hyderabad", "Ahmedabad", "Pune", "Jaipur", "Guwahati",
    "Patna", "Lucknow", "Bhubaneswar", "Thiruvananthapuram"
]


def update_tier1_weather_grid():
    """Refreshes live weather telemetry in the Tier 1 cache for Indian cities."""
    logger.info("[scheduler] Refreshing Tier 1 Location Weather Grid...")
    for city in MAJOR_INDIAN_METROS:
        try:
            weather_data = get_city_current_weather(city)
            set_location_weather(city, weather_data)
        except Exception as e:
            logger.warning(f"[scheduler] Failed telemetry update for {city}: {e}")
    logger.info("[scheduler] Tier 1 Weather Grid updated successfully.")


def run_ingestion_pipeline():
    """Runs all ingestion sources through the truth scoring engine."""
    logger.info("[scheduler] Starting Multi-Source Ingestion Pipeline...")
    db = SessionLocal()

    collectors = [
        ("IMD", IMDCollector()),
        ("GNews", GNewsCollector()),
        ("NewsData", NewsDataCollector()),
    ]

    total_ingested = 0
    total_verified = 0

    try:
        # First update telemetry grid
        update_tier1_weather_grid()

        for name, col in collectors:
            try:
                logger.info(f"[scheduler] Polling collector: {name}...")
                items = col.fetch()
                logger.info(f"[scheduler] {name} yielded {len(items)} items.")

                for item in items:
                    total_ingested += 1
                    res = process_and_verify_incident(
                        report_text=item.get("raw_text", ""),
                        city=item.get("city") or "Delhi",
                        state=item.get("state"),
                        latitude=item.get("latitude") or 28.6139,
                        longitude=item.get("longitude") or 77.2090,
                        event_type=item.get("event_type_guess"),
                        media_url=item.get("media_urls", [None])[0] if item.get("media_urls") else None,
                        source_id=2 if name == "IMD" else 3,
                        db=db,
                    )
                    if res.get("verification_status") == "Othentic":
                        total_verified += 1

            except Exception as e:
                logger.error(f"[scheduler] Collector {name} failed: {e}")

        logger.info(f"[scheduler] Cycle complete. Ingested: {total_ingested}, Verified: {total_verified}")

    finally:
        db.close()


def main_loop(interval_seconds: int = 300):
    """Runs continuous scheduled ingestion cycles."""
    logger.info(f"[scheduler] Scheduler started. Polling every {interval_seconds} seconds.")
    while True:
        try:
            run_ingestion_pipeline()
        except Exception as e:
            logger.error(f"[scheduler] Pipeline execution error: {e}")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    run_ingestion_pipeline()
