import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database_setup import SessionLocal
from app.services.verification_engine import process_and_verify_incident

def test_pipeline():
    db = SessionLocal()
    try:
        print("=== PIPELINE TEST 1: Instagram @Surya_12596841 (New Source) ===")
        # Note: We reset Surya_12596841 Total_Reports to 0 before this test
        from app.models import Source
        s = db.query(Source).filter(Source.Username == "Surya_12596841", Source.Platform == "Instagram").first()
        if s:
            s.Total_Reports = 0
            s.Warnings_Count = 0
            s.Fake_Reports = 0
            s.Trust_Status = "GREY"
            db.commit()

        res1 = process_and_verify_incident(
            report_text="Moderate rainfall reported in Kolkata Salt Lake area.",
            city="Kolkata",
            state="West Bengal",
            latitude=22.5726,
            longitude=88.3639,
            event_type="Rain",
            platform="Instagram",
            source_username="Surya_12596841",
            user_id=8,
            is_citizen_submission=True,
            db=db
        )
        s4_1 = next(item for item in res1["hint_breakdown"] if "Account & Source" in item["signal"])
        print(f"Result 1 -> Points: {s4_1['points']} | Status: {s4_1['status']}")
        assert s4_1["points"] == 2, f"Expected 2 points for new source, got {s4_1['points']}"

        print("\n=== PIPELINE TEST 2: news Hindustan news (RED-listed Source) ===")
        res2 = process_and_verify_incident(
            report_text="Extreme cyclone approaching Delhi with devastating storms.",
            city="Delhi",
            state="Delhi",
            latitude=28.6139,
            longitude=77.2090,
            event_type="Cyclone",
            platform="news",
            source_username="Hindustan news",
            user_id=8,
            is_citizen_submission=True,
            db=db
        )
        s4_2 = next(item for item in res2["hint_breakdown"] if "Account & Source" in item["signal"])
        print(f"Result 2 -> Points: {s4_2['points']} | Status: {s4_2['status']}")
        assert s4_2["points"] == 0, f"Expected 0 points for red listed source, got {s4_2['points']}"
        assert "RED-LISTED" in s4_2["status"], f"Expected RED-LISTED in status, got {s4_2['status']}"

        print("\n==============================================")
        print("PIPELINE END-TO-END VERIFICATION SUCCESSFUL!!")
        print("==============================================")
    finally:
        db.close()

if __name__ == "__main__":
    test_pipeline()
