import os
import sys
from unittest.mock import patch

# Ensure app is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database_setup import SessionLocal
from app.models import Source, User, Reports
from app.services.scoring import evaluate_verification_signals

def get_s4(res):
    return next(item for item in res["breakdown"] if "Account & Source" in item["signal"])

@patch("app.services.scoring.check_windy_strong_hint", return_value=True)
@patch("app.services.scoring.get_city_current_weather", return_value={"condition": "Rain", "precipitation_mm": 5.0, "wind_speed_kmh": 20.0})
@patch("app.services.scoring.imd_collector.get_district_warning", return_value={"has_warning": True, "severity": "Orange", "warning_type": "rainfall", "match_tier": "direct_district", "source": "IMD"})
@patch("app.services.scoring.verify_news_for_location", return_value=True)
def run_tests(mock_news, mock_imd, mock_weather, mock_windy):
    db = SessionLocal()
    try:
        print("=== TEST 1: New source in DB (Total_Reports=0) -> [Instagram] @Surya_12596841 ===")
        res1 = evaluate_verification_signals(
            city="Kolkata",
            state="West Bengal",
            latitude=22.5726,
            longitude=88.3639,
            event_type="Rain",
            user_trust_status="GREY",
            is_first_post=True,
            platform="Instagram",
            source_username="Surya_12596841",
            user_id=8, # Logged-in citizen user Surya
            db_session=db
        )
        s4_1 = get_s4(res1)
        print(f"Points: {s4_1['points']} | Passed: {s4_1['passed']} | Status: {s4_1['status']}")
        assert s4_1["points"] == 2, f"Expected 2, got {s4_1['points']}"

        print("\n=== TEST 2: Brand new source not yet in DB -> [Twitter] @brand_new_bot_999 ===")
        res2 = evaluate_verification_signals(
            city="Mumbai",
            state="Maharashtra",
            latitude=19.0760,
            longitude=72.8777,
            event_type="Rain",
            user_trust_status="GREY",
            is_first_post=True,
            platform="Twitter",
            source_username="@brand_new_bot_999",
            user_id=8,
            db_session=db
        )
        s4_2 = get_s4(res2)
        print(f"Points: {s4_2['points']} | Passed: {s4_2['passed']} | Status: {s4_2['status']}")
        assert s4_2["points"] == 2, f"Expected 2, got {s4_2['points']}"

        print("\n=== TEST 3: RED-listed source in DB -> [news] Hindustan news ===")
        res3 = evaluate_verification_signals(
            city="Delhi",
            state="Delhi",
            latitude=28.6139,
            longitude=77.2090,
            event_type="Heatwave",
            user_trust_status="GREY",
            is_first_post=False,
            platform="news",
            source_username="Hindustan news",
            user_id=8, # Even if reported by Surya
            db_session=db
        )
        s4_3 = get_s4(res3)
        print(f"Points: {s4_3['points']} | Passed: {s4_3['passed']} | Status: {s4_3['status']}")
        assert s4_3["points"] == 0, f"Expected 0, got {s4_3['points']}"
        assert "RED-LISTED" in s4_3["status"], f"Expected RED-LISTED in status, got {s4_3['status']}"

        print("\n=== TEST 4: RED-listed source with leading @ -> [news] @Hindustan news ===")
        res4 = evaluate_verification_signals(
            city="Delhi",
            state="Delhi",
            latitude=28.6139,
            longitude=77.2090,
            event_type="Heatwave",
            user_trust_status="GREY",
            is_first_post=False,
            platform="news",
            source_username="@Hindustan news",
            user_id=8,
            db_session=db
        )
        s4_4 = get_s4(res4)
        print(f"Points: {s4_4['points']} | Passed: {s4_4['passed']} | Status: {s4_4['status']}")
        assert s4_4["points"] == 0, f"Expected 0, got {s4_4['points']}"
        assert "RED-LISTED" in s4_4["status"], f"Expected RED-LISTED in status, got {s4_4['status']}"

        print("\n=== TEST 5: Verified social source in DB -> [FaceBook] Surya ellen ===")
        res5 = evaluate_verification_signals(
            city="Kolkata",
            state="West Bengal",
            latitude=22.5726,
            longitude=88.3639,
            event_type="Rain",
            user_trust_status="GREEN",
            is_first_post=False,
            platform="FaceBook",
            source_username="Surya ellen",
            user_id=8,
            db_session=db
        )
        s4_5 = get_s4(res5)
        print(f"Points: {s4_5['points']} | Passed: {s4_5['passed']} | Status: {s4_5['status']}")
        assert s4_5["points"] == 10, f"Expected 10, got {s4_5['points']}"

        print("\n=== TEST 6: Direct Citizen submission by established user Surya (ID: 8) ===")
        res6 = evaluate_verification_signals(
            city="Kolkata",
            state="West Bengal",
            latitude=22.5726,
            longitude=88.3639,
            event_type="Rain",
            user_trust_status="GREEN",
            is_first_post=False,
            platform="Citizen",
            source_username="Surya allen",
            user_id=8,
            db_session=db
        )
        s4_6 = get_s4(res6)
        print(f"Points: {s4_6['points']} | Passed: {s4_6['passed']} | Status: {s4_6['status']}")
        assert s4_6["points"] == 10, f"Expected 10, got {s4_6['points']}"

        print("\n=== TEST 7: Direct Citizen submission by user with 0 past reports ===")
        new_user = db.query(User).filter(User.Email == "deyc892@gmail.com").first()
        if not new_user:
            new_user = User(Name="Test New User", Email="test_new_user_temp@example.com", Password_Hash="x")
            db.add(new_user)
            db.commit()
        res7 = evaluate_verification_signals(
            city="Kolkata",
            state="West Bengal",
            latitude=22.5726,
            longitude=88.3639,
            event_type="Rain",
            user_trust_status="GREY",
            is_first_post=True,
            platform="Citizen",
            source_username=new_user.Name,
            user_id=new_user.Id,
            db_session=db
        )
        s4_7 = get_s4(res7)
        print(f"Points: {s4_7['points']} | Passed: {s4_7['passed']} | Status: {s4_7['status']}")
        assert s4_7["points"] == 2, f"Expected 2, got {s4_7['points']}"

        print("\n======================================")
        print("ALL 7 SIGNAL 4 TESTS PASSED PERFECTLY!")
        print("======================================")

    finally:
        db.close()

if __name__ == "__main__":
    run_tests()
