import sys
import pprint

sys.path.insert(0, ".")

from app.database_setup import SessionLocal
from app.services.verification_engine import process_and_verify_incident

def run():
    db = SessionLocal()
    try:
        img_path = r"C:\Users\sdey9\.gemini\antigravity-ide\brain\8db65b31-df2d-44d7-8834-8cf29bb2a0c2\.user_uploaded\media_1789070793162.jpg"
        with open(img_path, "rb") as f:
            img_bytes = f.read()

        res = process_and_verify_incident(
            report_text="Heavy monsoon rainfall causing waterlogged roads in Patna market area.",
            city="Patna",
            state="Bihar",
            latitude=25.5941,
            longitude=85.1376,
            event_type="Rain",
            platform="Citizen",
            source_username="Surya allen",
            media_bytes=img_bytes,
            filename="real_rain_patna.jpg",
            user_id=8,
            is_citizen_submission=True,
            db=db,
        )
        print("\n=== PIPELINE RESULT FOR REAL USER IMAGE ===")
        print("Status:", res.get("verification_status"))
        print("Score:", res.get("verification_score"))
        print("Is AI Generated:", res.get("is_ai_generated"))
        print("\nBreakdown:")
        pprint.pprint(res.get("hint_breakdown"))

        assert res.get("is_ai_generated") is not True, "Real image was falsely marked as AI generated!"
        print("\nSUCCESS: Real image cleanly passed verification without AI rejection!")
    finally:
        db.close()

if __name__ == "__main__":
    run()
