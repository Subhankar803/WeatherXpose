import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database_setup import SessionLocal
from app.services.verification_engine import process_and_verify_incident

def test_earthquake_report():
    db = SessionLocal()
    try:
        result = process_and_verify_incident(
            report_text="Heavy Earthquake in delhi",
            city="Delhi",
            state="Delhi",
            latitude=28.6139,
            longitude=77.2090,
            event_type="Heavy Rainfall", # User mistakenly left dropdown on Heavy Rainfall!
            platform="Facebook",
            source_username="Beast",
            db=db
        )
        print("=== VERIFICATION RESULT ===")
        print(f"Event Type: {result.get('event_type')}")
        print(f"Verification Status: {result.get('verification_status')}")
        print(f"Verification Score: {result.get('verification_score')}")
        print(f"Summary: {result.get('summary_reason')}")
        print("\n=== BREAKDOWN ===")
        for b in result.get("hint_breakdown", []):
            print(f"- {b.get('signal')}: {b.get('points')} pts ({b.get('status')})")

    finally:
        db.close()

if __name__ == "__main__":
    test_earthquake_report()
