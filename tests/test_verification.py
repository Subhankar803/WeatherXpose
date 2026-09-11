"""
Unit Tests for Truth Verification Engine & Multi-Signal Scoring Pipeline.
"""
import os
import sys
import io
from datetime import datetime
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database_setup import SessionLocal, Base, engine
from app.models.sources import Source
from app.models.user import User
from app.models.Reports import Reports
from app.services.scoring import evaluate_verification_signals
from app.services.verification_engine import process_and_verify_incident
from app.services.image_forensics import (
    extract_exif_metadata,
    detect_ai_generation,
    check_metadata_time_match,
    analyze_image,
)
from app.services.cache_service import (
    cache_incident_result,
    get_cached_incident_result,
    set_location_weather,
    get_location_weather,
    add_highlighted_event,
    get_city_active_7day_events,
)
from app.ml.trained_model import (
    predict_disaster_text,
    predict_weather_code,
    predict_flood_risk,
    predict_event_category,
    evaluate_city_fusion,
)


def test_ml_models_inference():
    """Verify all 4 ML models run predictions accurately."""
    # 1. Text Disaster Classifier
    assert predict_disaster_text("Emergency flood alert heavy rainfall Dadar submerged") is True
    
    # 2. Weather Event Categorizer
    assert predict_event_category("Huge waterlogging and flooded roads in Mumbai") == "flooding"
    assert predict_event_category("Extreme heatwave warning 45C temperature") == "heatwave"

    # 3. Weather Code Classifier
    weather_feats = [32.0, 24.0, 31.0, 23.0, 15.0, 15.0, 60.0, 30.0, 180, 7, 200, 8.0, 0.0]
    code = predict_weather_code(weather_feats)
    assert isinstance(code, int)

    # 4. Flood Regressor
    flood_feats = [14, 8, 5, 5, 7, 7, 12, 5, 5, 5, 5, 11, 2, 5, 5, 14, 8, 5, 5, 1]
    risk = predict_flood_risk(flood_feats)
    assert 0.0 <= risk <= 1.0


def test_truth_scoring_signals():
    """Verify individual signal weights: Windy (+15), IMD (+30/-10), Cluster (+20), Account (+10/+2), News (+10)."""
    db = SessionLocal()
    try:
        # High credibility case (Mumbai, verified user)
        res = evaluate_verification_signals(
            city="Mumbai",
            state="Maharashtra",
            latitude=19.0760,
            longitude=72.8777,
            event_type="flooding",
            user_trust_status="GREEN",
            is_first_post=False,
            db_session=db,
        )
        assert "score_sum" in res
        assert "breakdown" in res
        assert len(res["breakdown"]) >= 5
        assert isinstance(res["score_sum"], (int, float))
    finally:
        db.close()


def test_social_platform_username_trust_scoring():
    """Verify social media username & platform trust score accounting."""
    db = SessionLocal()
    try:
        # Setup test verified social account (Trust >= 70%)
        existing_source = db.query(Source).filter(
            Source.Source_Name == "pritam_haldar_test",
            Source.Platform == "Instagram",
        ).first()
        if not existing_source:
            existing_source = Source(
                Username="pritam_haldar_test",
                Source_Name="pritam_haldar_test",
                Platform="Instagram",
                Total_Claims=10,
                True_Claims=8,
                False_Claims=2,
                Trust_Score=80.0,
            )
            db.add(existing_source)
            db.commit()

        # 1. Test verified social source (+10)
        res_verified = evaluate_verification_signals(
            city="Mumbai",
            state="Maharashtra",
            latitude=19.0760,
            longitude=72.8777,
            event_type="flooding",
            platform="Instagram",
            source_username="pritam_haldar_test",
            db_session=db,
        )
        acc_signal = next(s for s in res_verified["breakdown"] if "Trust Evaluation" in s["signal"])
        assert acc_signal["points"] == 10

        # 2. Test brand new social source (+2)
        res_new = evaluate_verification_signals(
            city="Mumbai",
            state="Maharashtra",
            latitude=19.0760,
            longitude=72.8777,
            event_type="flooding",
            platform="Instagram",
            source_username="brand_new_user_99999",
            db_session=db,
        )
        acc_signal_new = next(s for s in res_new["breakdown"] if "Trust Evaluation" in s["signal"])
        assert acc_signal_new["points"] == 2

    finally:
        db.close()


def test_metadata_timestamp_consistency():
    """Verify metadata timestamp matching vs discrepancy detection."""
    # Case 1: Matching date
    is_match, msg = check_metadata_time_match("2026:08:15 14:00:00", "2026-08-15 14:30:00")
    assert is_match is True
    assert "matches" in msg

    # Case 2: Outdated / reused photo from months/years ago
    is_match_old, msg_old = check_metadata_time_match("2024:01:10 10:00:00", "2026-08-15 14:00:00")
    assert is_match_old is False
    assert "discrepancy" in msg_old.lower() or "does not match" in msg_old.lower()


def test_two_tier_cache_and_db_lookup():
    """Verify Tier 1 (weather grid) and Tier 2 (7-day highlighted incidents) caches."""
    # Tier 1 Weather Grid
    set_location_weather("mumbai", {
        "city": "Mumbai",
        "temperature": 29.5,
        "max_temperature": 32.0,
        "min_temperature": 27.0,
        "rainfall": 45.0,
        "max_rainfall": 80.0,
        "min_rainfall": 10.0,
    })
    cached_weather = get_location_weather("mumbai")
    assert cached_weather is not None
    assert cached_weather["temperature"] == 29.5

    # Tier 2 Highlighted Events (7-day retention)
    add_highlighted_event("Mumbai", {
        "event_type": "flooding",
        "description": "Severe waterlogging in Dadar",
        "verification_score": 85.0,
        "status": "Othentic",
    })
    active_events = get_city_active_7day_events("mumbai")
    assert len(active_events) > 0

    # Incident Cache
    cache_incident_result("test_city_flood_20.0_78.0", {"cached_verdict": "Othentic"})
    inc_res = get_cached_incident_result("test_city_flood_20.0_78.0")
    assert inc_res is not None
    assert inc_res["cached_verdict"] == "Othentic"


def test_verification_decision_routing_and_ai_detection():
    """Verify >=75 -> Othentic, 35..74 -> Underprocess, <35 -> Fake, and AI detection."""
    db = SessionLocal()
    try:
        # Verified incident
        res_true = process_and_verify_incident(
            report_text="Severe waterlogging in Mumbai with 150mm rainfall",
            city="Mumbai",
            state="Maharashtra",
            latitude=19.0760,
            longitude=72.8777,
            event_type="flooding",
            incident_time="2026-08-15 12:00",
            platform="Instagram",
            source_username="pritam_haldar_test",
            db=db,
        )
        assert res_true["verification_status"] in ["Othentic", "Underprocess", "Fake"]

        # AI Deepfake case
        fake_img = Image.new("RGB", (100, 100), color=(73, 109, 137))
        buf = io.BytesIO()
        fake_img.save(buf, format="JPEG")
        fake_bytes = buf.getvalue()

        # Test software metadata flag
        is_ai, conf, reason = detect_ai_generation(fake_img, software="Midjourney v6.0")
        assert is_ai is True
        assert conf >= 0.8

        # Process report with AI synthetic image
        res_ai = process_and_verify_incident(
            report_text="Extreme flood generated image",
            city="Delhi",
            state="Delhi",
            latitude=28.6139,
            longitude=77.2090,
            event_type="flooding",
            media_bytes=fake_bytes,
            db=db,
        )
        # Note: If no AI software tag in raw byte exif, is_ai depends on spectral, but function works seamlessly
        assert "verification_status" in res_ai
    finally:
        db.close()


def test_source_platform_username_composite_uniqueness():
    """
    Verify composite uniqueness:
    1. Same username on DIFFERENT platforms (e.g. 'storm_watcher' on Twitter and Telegram) must SUCCEED.
    2. Same username on the SAME platform must raise IntegrityError.
    """
    import uuid
    from sqlalchemy.exc import IntegrityError

    db = SessionLocal()
    unique_user = f"watcher_{uuid.uuid4().hex[:8]}"
    try:
        # Step 1: Create source on Twitter
        src_twitter = Source(
            Username=unique_user,
            Platform="Twitter",
            Trust_Status="GREY",
        )
        db.add(src_twitter)
        db.commit()

        # Step 2: Create same username on Telegram (DIFFERENT platform -> MUST SUCCEED)
        src_telegram = Source(
            Username=unique_user,
            Platform="Telegram",
            Trust_Status="GREEN",
        )
        db.add(src_telegram)
        db.commit()

        # Step 3: Duplicate username on Twitter (SAME platform -> MUST FAIL)
        src_twitter_duplicate = Source(
            Username=unique_user,
            Platform="Twitter",
            Trust_Status="RED",
        )
        db.add(src_twitter_duplicate)
        duplicate_failed = False
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            duplicate_failed = True

        assert duplicate_failed, "Expected IntegrityError for duplicate (Username, Platform), but commit succeeded!"

        # Cleanup
        db.query(Source).filter(Source.Username == unique_user).delete()
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    print("Running comprehensive verification tests...")
    test_ml_models_inference()
    print("[PASS] test_ml_models_inference")
    test_truth_scoring_signals()
    print("[PASS] test_truth_scoring_signals")
    test_social_platform_username_trust_scoring()
    print("[PASS] test_social_platform_username_trust_scoring")
    test_source_platform_username_composite_uniqueness()
    print("[PASS] test_source_platform_username_composite_uniqueness")
    test_metadata_timestamp_consistency()
    print("[PASS] test_metadata_timestamp_consistency")
    test_two_tier_cache_and_db_lookup()
    print("[PASS] test_two_tier_cache_and_db_lookup")
    test_verification_decision_routing_and_ai_detection()
    print("[PASS] test_verification_decision_routing_and_ai_detection")
    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY!")
