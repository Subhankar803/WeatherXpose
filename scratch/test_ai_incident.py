import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database_setup import SessionLocal
from app.services.verification_engine import process_and_verify_incident

def test_ai_incident():
    img_path = r"C:\Users\sdey9\.gemini\antigravity-ide\brain\8db65b31-df2d-44d7-8834-8cf29bb2a0c2\.user_uploaded\media_1789081732416.jpg"
    with open(img_path, "rb") as f:
        media_bytes = f.read()

    db = SessionLocal()
    try:
        res = process_and_verify_incident(
            report_text="Heavy rain and flood in Kolkata College Street",
            city="Kolkata",
            state="West Bengal",
            latitude=22.5726,
            longitude=88.3639,
            event_type="Flood",
            media_bytes=media_bytes,
            filename="kolkata_flood_street.jpg",
            platform="Facebook",
            source_username="Beast",
            db=db
        )
        print("=== VERIFICATION RESULT ===")
        print("Verification Status:", res.get("verification_status"))
        print("Verification Score:", res.get("verification_score"))
        print("Is AI Generated:", res.get("is_ai_generated"))
        print("AI Confidence:", res.get("ai_confidence"))
        print("AI Reason:", res.get("ai_reason"))
        print("Verdict Summary:", res.get("verdict_summary"))
    finally:
        db.close()

if __name__ == "__main__":
    test_ai_incident()
