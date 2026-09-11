import sys
sys.path.insert(0, ".")

from app.database_setup import SessionLocal
from app.services.scoring import evaluate_verification_signals

def test_windy_imd():
    db = SessionLocal()
    try:
        cities = [
            ("Mumbai", "Maharashtra", 19.0760, 72.8777, "Rain"),
            ("Pune", "Maharashtra", 18.5204, 73.8567, "Rain"),
            ("Chennai", "Tamil Nadu", 13.0827, 80.2707, "Rain"),
            ("Kolkata", "West Bengal", 22.5726, 88.3639, "Rain"),
            ("Delhi", "Delhi", 28.6139, 77.2090, "Heatwave"),
        ]

        print("=== EVALUATING WINDY & IMD SIGNALS IN SCORING ENGINE ===")
        for city, state, lat, lon, ev in cities:
            res = evaluate_verification_signals(
                city=city,
                state=state,
                latitude=lat,
                longitude=lon,
                event_type=ev,
                user_trust_status="GREEN",
                is_first_post=False,
                platform="Citizen",
                source_username="citizen",
                user_id=8,
                db_session=db
            )
            s1 = next(item for item in res["breakdown"] if "Atmospheric" in item["signal"])
            s2 = next(item for item in res["breakdown"] if "IMD" in item["signal"])
            print(f"\nLocation: {city}, {state} (Event: {ev})")
            print(f"  Signal 1 (Windy/OpenWeather): Points: {s1['points']} | Passed: {s1['passed']} | {s1['status']}")
            print(f"  Signal 2 (IMD Official):      Points: {s2['points']} | Passed: {s2['passed']} | {s2['status']}")
            print(f"  Total Incident Score: {res['score_sum']}")
            # Ensure IMD points are not negative when Windy/Atmospheric passes
            if s1['passed']:
                assert s2['points'] >= 0, f"IMD score was negative ({s2['points']}) while Windy passed!"

        print("\n=======================================================")
        print("ALL WINDY + IMD SCORING ENGINE CHECKS PASSED!")
        print("=======================================================")
    finally:
        db.close()

if __name__ == "__main__":
    test_windy_imd()
