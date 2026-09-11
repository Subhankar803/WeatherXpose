import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database_setup import SessionLocal
from app.services.verification_engine import process_and_verify_incident

def test_same_case_different_users():
    db = SessionLocal()
    users_to_test = [
        {"platform": "Facebook", "username": "Beast", "user_id": None},
        {"platform": "Facebook", "username": "RandomUser123", "user_id": None},
        {"platform": "Citizen", "username": "JohnDoe", "user_id": 1},
        {"platform": "X", "username": "CitizenReporter", "user_id": None},
    ]

    print("--- TESTING EARTHQUAKE IN DELHI (SHOULD ALL BE IDENTICAL FAKE) ---")
    eq_scores = []
    for u in users_to_test:
        res = process_and_verify_incident(
            report_text="Heavy Earthquake in delhi",
            city="Delhi",
            state="Delhi",
            latitude=28.6139,
            longitude=77.2090,
            event_type="Earthquake",
            platform=u["platform"],
            source_username=u["username"],
            user_id=u["user_id"],
            db=db
        )
        eq_scores.append(res["verification_score"])
        print(f"User [{u['platform']} / {u['username']}]: Score = {res['verification_score']}, Status = {res['verification_status']}")

    print("\n--- TESTING HEAVY RAINFALL IN MUMBAI (SHOULD ALL BE IDENTICAL) ---")
    rain_scores = []
    for u in users_to_test:
        res = process_and_verify_incident(
            report_text="Heavy rainfall in Mumbai today",
            city="Mumbai",
            state="Maharashtra",
            latitude=19.0760,
            longitude=72.8777,
            event_type="Heavy Rainfall",
            platform=u["platform"],
            source_username=u["username"],
            user_id=u["user_id"],
            db=db
        )
        rain_scores.append(res["verification_score"])
        print(f"User [{u['platform']} / {u['username']}]: Score = {res['verification_score']}, Status = {res['verification_status']}")

    db.close()

    assert len(set(eq_scores)) == 1, f"Earthquake scores differed across users! {eq_scores}"
    assert len(set(rain_scores)) == 1, f"Rain scores differed across users! {rain_scores}"
    print("\nSUCCESS: All users receive the EXACT same score for the same case!")

if __name__ == "__main__":
    test_same_case_different_users()
