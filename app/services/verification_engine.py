"""
National Weather Verification Engine.

Orchestrates:
1. Two-tier Cache & DB lookup (deduplication & instant retrieval)
2. Image Forensics & AI Generation / Deepfake Detection
3. Multi-Signal Scoring Engine (+15 Windy, +30/-10 IMD, +20 Cluster, +10/+2/+0 Account, +10 News)
4. Decision Thresholds:
   - sum >= 75 -> VERIFIED (Othentic) + User Promoted to GREEN
   - 35 <= sum < 75 -> UNDERPROCESS (Routed to Admin Panel Queue)
   - sum < 35 -> FAKE + Account Penalties (GREY/RED List, Block User)
5. Synchronous update to DB and Two-Tier Redis Cache (Tier 1 & Tier 2 7-day window)
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models import Reports, Images_Videos, User, Source
from app.services.image_forensics import analyze_image
from app.services.scoring import evaluate_verification_signals
from app.services.cache_service import (
    get_cached_incident_result,
    cache_incident_result,
    add_highlighted_event,
    set_location_weather,
)
from app.ml.event_classifier import classify_event

logger = logging.getLogger(__name__)


def process_and_verify_incident(
    report_text: str,
    city: str,
    state: Optional[str] = None,
    latitude: float = 20.5937,
    longitude: float = 78.9629,
    event_type: Optional[str] = None,
    incident_time: Optional[str] = None,
    platform: Optional[str] = None,
    source_username: Optional[str] = None,
    media_bytes: Optional[bytes] = None,
    media_url: Optional[str] = None,
    filename: Optional[str] = None,
    user_id: Optional[int] = None,
    source_id: Optional[int] = None,
    is_citizen_submission: bool = False,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Unified Verification Workflow:
    - Checks incident cache / DB deduplication
    - Verifies telemetry against OpenWeather & Windy API (Wind, Rain, Storm)
    - Verifies against IMD Bulletins and Nowcasts
    - Checks Image Forensics (Metadata, Error Level Analysis, Deepfake detection)
    - Calculates Multi-Signal Verification Score (0 - 100)
    - Updates User / Source Trust Score
    - Persists report into database
    """
    logger.info(f"[verification_engine] Starting verification for '{city}' | Event: {event_type} | CitizenSubmission: {is_citizen_submission}")
    
    city_clean = city.strip().title()
    # Resolve state automatically if not provided or set to generic India
    from app.utils.geo_utils import resolve_state_for_city_or_coords
    if not state or state.strip().lower() in ["india", "unknown", "none", ""]:
        state_clean = resolve_state_for_city_or_coords(city_clean, latitude, longitude)
    else:
        state_clean = state.strip().title()
    
    # 0. Determine event category
    # If report_text explicitly claims a high-specificity disaster (e.g. earthquake, tsunami, landslide, cyclone)
    # that contradicts the generic dropdown selection, the user's explicit textual claim takes precedence.
    text_claimed_event = classify_event(report_text)
    if not event_type or event_type.lower() in ["unknown", "general", "none", "", "other"]:
        event_type = text_claimed_event
    elif text_claimed_event in ["earthquake", "tsunami", "landslide", "cyclone", "heatwave"] and text_claimed_event.lower() != event_type.lower():
        logger.info(f"[verification_engine] Explicit text claim '{text_claimed_event}' takes precedence over dropdown '{event_type}'.")
        event_type = text_claimed_event

    # 1. CHECK PERSISTENT DISK / REDIS INCIDENT CACHE
    date_part = str(incident_time)[:10].strip() if incident_time else ""
    cache_lookup_key = f"{city_clean.lower()}_{event_type.lower()}_{round(latitude, 2)}_{round(longitude, 2)}"
    if date_part:
        cache_lookup_key += f"_{date_part}"
    if not media_bytes:
        cached_result = get_cached_incident_result(cache_lookup_key)
        if cached_result:
            logger.info(f"[verification_engine] Cache HIT for {cache_lookup_key}")
            cached_result["from_cache"] = True
            return cached_result

    # 2. CHECK DATABASE FOR MATCHING INCIDENT
    # Only short-circuit for automated crawler ingestion if no fresh media is present
    if not is_citizen_submission and db and not media_bytes and not user_id:
        try:
            existing_db_report = db.query(Reports).filter(
                Reports.City == city_clean,
                Reports.Event_Type == event_type,
            ).order_by(Reports.Id.desc()).first()
            if existing_db_report and (datetime.utcnow() - existing_db_report.Time).total_seconds() < 7200:
                logger.info(f"[verification_engine] Database HIT for {city_clean} #{existing_db_report.Id}")
                return {
                    "report_id": existing_db_report.Id,
                    "city": existing_db_report.City,
                    "state": existing_db_report.State,
                    "latitude": existing_db_report.Latitude,
                    "longitude": existing_db_report.Longitude,
                    "event_type": existing_db_report.Event_Type,
                    "verification_status": existing_db_report.Verification_Status,
                    "verification_score": existing_db_report.Verification_Score,
                    "hint_breakdown": json.loads(existing_db_report.Hint_Breakdown) if existing_db_report.Hint_Breakdown else [],
                    "from_database": True,
                    "from_cache": False,
                    "message": "Incident already researched and recorded in database.",
                }
        except Exception as e:
            logger.warning(f"DB lookup error: {e}")

    # Retrieve User state
    user_obj = None
    if db and user_id:
        user_obj = db.query(User).filter(User.Id == user_id).first()

    # Retrieve or initialize Source row (Social Media or Citizen Portal)
    source_obj = None
    clean_platform_str = (platform or "Citizen").strip()
    is_external_report = clean_platform_str.lower() not in ["citizen", "citizenportal", "direct", "dashboardchat", ""]

    if db and is_external_report and source_username:
        source_clean_name = source_username.strip()
        raw_handle = source_clean_name.lstrip("@").strip()
        platform_clean = clean_platform_str
        source_obj = db.query(Source).filter(
            (
                Source.Username.ilike(source_clean_name) |
                Source.Username.ilike(raw_handle) |
                Source.Username.ilike(f"@{raw_handle}") |
                Source.Source_Name.ilike(source_clean_name) |
                Source.Source_Name.ilike(raw_handle)
            ),
            Source.Platform.ilike(platform_clean),
        ).first()
        if not source_obj:
            source_obj = Source(
                Username=raw_handle,
                Source_Name=source_clean_name,
                Platform=platform_clean,
                Trust_Status="GREY",
                Total_Reports=0,
                Fake_Reports=0,
                Warnings_Count=0,
                Total_Claims=0,
                True_Claims=0,
                False_Claims=0,
                Trust_Score=50.0,
                First_Seen=datetime.utcnow(),
                Last_Seen=datetime.utcnow(),
            )
            db.add(source_obj)
            db.flush()
        source_id = source_obj.Id

    # Ensure CitizenPortal source for the logged-in user always exists and is synchronized
    portal_src = None
    if db and user_obj:
        portal_src = db.query(Source).filter(
            Source.Username == user_obj.Email,
            Source.Platform == "CitizenPortal",
        ).first()
        if not portal_src:
            portal_src = Source(
                Username=user_obj.Email,
                Source_Name=user_obj.Name or user_obj.Email,
                Platform="CitizenPortal",
                Trust_Status="GREEN" if db.query(Reports).filter(Reports.User_Id == user_obj.Id, Reports.Verification_Status == "Othentic").count() >= 1 else "GREY",
                Total_Reports=db.query(Reports).filter(Reports.User_Id == user_obj.Id).count(),
                Fake_Reports=db.query(Reports).filter(Reports.User_Id == user_obj.Id, Reports.Verification_Status == "Fake").count(),
                Warnings_Count=0,
                Total_Claims=db.query(Reports).filter(Reports.User_Id == user_obj.Id).count(),
                True_Claims=db.query(Reports).filter(Reports.User_Id == user_obj.Id, Reports.Verification_Status != "Fake").count(),
                False_Claims=db.query(Reports).filter(Reports.User_Id == user_obj.Id, Reports.Verification_Status == "Fake").count(),
                Trust_Score=100.0,
                First_Seen=user_obj.Created_at or datetime.utcnow(),
                Last_Seen=datetime.utcnow(),
            )
            db.add(portal_src)
            db.flush()
        if not source_obj:
            source_obj = portal_src
            source_id = portal_src.Id

    if is_external_report:
        is_first_post = ((source_obj.Total_Reports or 0) == 0) if source_obj else True
        source_trust_status = source_obj.Trust_Status if source_obj else "GREY"
    elif user_obj and db:
        user_past_reports = db.query(Reports).filter(Reports.User_Id == user_obj.Id).count()
        is_first_post = (user_past_reports == 0)
        source_trust_status = portal_src.Trust_Status if portal_src else "GREY"
    else:
        is_first_post = ((source_obj.Total_Reports or 0) == 0) if source_obj else True
        source_trust_status = source_obj.Trust_Status if source_obj else "GREY"

    # 3. IMAGE & VIDEO FORENSICS / AI-GENERATED CHECK
    forensics_info = None
    is_ai_fake = False
    ai_score = 0.0
    img_hash = "0000000000000000"
    meta_time_match = True
    meta_time_diag = None

    if media_bytes:
        forensics_info = analyze_image(media_bytes, filename=filename, incident_time=incident_time)
        is_ai_fake = forensics_info.get("is_ai_generated", False)
        ai_score = forensics_info.get("ai_score", 0.0)
        img_hash = forensics_info.get("img_hash", "0000000000000000")
        meta_time_match = forensics_info.get("metadata_time_match", True)
        meta_time_diag = forensics_info.get("metadata_time_diagnostic")

    # If media is AI-generated / Deepfake -> Immediate FALSE Event
    if is_ai_fake:
        verdict_status = "Fake"
        final_score = 0.0
        breakdown = [{
            "signal": "Image & Media Forensics",
            "weight": "FAIL",
            "points": 0,
            "passed": False,
            "status": f"AI-Generated synthetic media detected (Confidence: {int(ai_score * 100)}%) - {forensics_info.get('ai_reason')}"
        }]
        
        # Source penalty logic (Reputation metrics live on Source)
        penalty_msg = "Disinformation flagged; unverified / synthetic media rejected."
        if source_obj and db:
            source_obj.Total_Reports = (source_obj.Total_Reports or 0) + 1
            source_obj.Fake_Reports = (source_obj.Fake_Reports or 0) + 1
            source_obj.Warnings_Count = (source_obj.Warnings_Count or 0) + 1
            source_obj.Total_Claims = (source_obj.Total_Claims or 0) + 1
            source_obj.False_Claims = (source_obj.False_Claims or 0) + 1
            source_obj.Trust_Score = round((source_obj.True_Claims / max(1, source_obj.Total_Claims)) * 100.0, 1)
            source_obj.Last_Seen = datetime.utcnow()

            if source_obj.Trust_Status == "RED" or source_obj.Warnings_Count >= 3:
                source_obj.Trust_Status = "RED"
                penalty_msg = f"SOURCE [{source_obj.Platform}] @{source_obj.Username} BLOCKED & PLACED ON RED LIST (Repeated Misinformation / AI Synthetic Fake)"
            elif source_obj.Trust_Status == "GREEN":
                source_obj.Trust_Status = "GREY"
                penalty_msg = "Warning issued to verified source; trust status downgraded to GREY."
            else:
                source_obj.Trust_Status = "GREY"
                penalty_msg = "Warning issued; source placed on GREY monitoring list."
            db.commit()

        # Save to DB & Cache
        saved_report_id = _save_report_to_db(
            db=db, user_id=user_id, source_id=source_id, report_text=report_text,
            incident_time=incident_time, city=city_clean, state=state_clean, lat=latitude, lon=longitude,
            event_type=event_type, media_url=media_url, score=final_score,
            status=verdict_status, breakdown=breakdown, is_ai=1,
            forensics=forensics_info,
        )

        res = {
            "report_id": saved_report_id,
            "city": city_clean,
            "state": state_clean,
            "latitude": latitude,
            "longitude": longitude,
            "event_type": event_type,
            "verification_status": verdict_status,
            "verification_score": final_score,
            "hint_breakdown": breakdown,
            "is_ai_generated": True,
            "ai_confidence": ai_score,
            "ai_reason": forensics_info.get("ai_reason") if forensics_info else "Synthetic media detected",
            "penalty_action": penalty_msg,
            "from_cache": False,
            "from_database": False,
            "verdict_summary": "Report REJECTED: Synthetic AI-generated weather visual.",
        }
        cache_incident_result(cache_lookup_key, res)
        return res

    # 4. CALCULATE MULTI-SIGNAL SCORE (`sum`)
    signal_results = evaluate_verification_signals(
        city=city_clean,
        state=state_clean,
        latitude=latitude,
        longitude=longitude,
        event_type=event_type,
        user_trust_status=source_trust_status,
        is_first_post=is_first_post,
        platform=platform,
        source_username=source_username,
        user_id=user_id,
        metadata_time_match=meta_time_match,
        metadata_time_diagnostic=meta_time_diag,
        db_session=db,
        incident_time=incident_time,
    )

    score_sum = signal_results["score_sum"]
    breakdown = signal_results["breakdown"]

    # 5. FINAL DECISION ROUTING
    # Rule: Score > 60 -> Auto Verified (Othentic)
    #       Score 27..60 -> Sent to Admin Portal for manual review (Underprocess)
    #       Score < 27   -> Auto Rejected (Fake)
    if score_sum > 60:
        verdict_status = "Othentic"
        verdict_summary = "VERIFIED TRUE WEATHER INCIDENT: Highly corroborated across atmospheric & official signals (Score > 60)."
        
        # Source Promotion (Metrics live on Source)
        if source_obj and db:
            source_obj.Total_Reports = (source_obj.Total_Reports or 0) + 1
            source_obj.Total_Claims = (source_obj.Total_Claims or 0) + 1
            source_obj.True_Claims = (source_obj.True_Claims or 0) + 1
            source_obj.Trust_Status = "GREEN"  # Promoted to Verified
            source_obj.Trust_Score = round(((source_obj.Total_Reports - (source_obj.Fake_Reports or 0)) / max(1, source_obj.Total_Reports)) * 100.0, 1)
            source_obj.Last_Seen = datetime.utcnow()

        if portal_src and db:
            portal_src.Total_Reports = (portal_src.Total_Reports or 0) + 1
            portal_src.Total_Claims = (portal_src.Total_Claims or 0) + 1
            portal_src.True_Claims = (portal_src.True_Claims or 0) + 1
            portal_src.Trust_Status = "GREEN"
            portal_src.Trust_Score = round(((portal_src.Total_Reports - (portal_src.Fake_Reports or 0)) / max(1, portal_src.Total_Reports)) * 100.0, 1)
            portal_src.Last_Seen = datetime.utcnow()
        if db:
            db.commit()

        # Update Tier 2 Highlighted 7-Day Event Cache
        add_highlighted_event(city_clean, {
            "city": city_clean,
            "state": state_clean,
            "latitude": latitude,
            "longitude": longitude,
            "event_type": event_type,
            "description": report_text,
            "verification_score": score_sum,
            "status": verdict_status,
            "timestamp": incident_time or datetime.utcnow().isoformat(),
        })

    elif 27 <= score_sum <= 60:
        verdict_status = "Underprocess"
        verdict_summary = "AMBIGUOUS INCIDENT: Sent to Admin Panel review queue for manual forensic audit (Score 27-60)."
        if source_obj and db:
            source_obj.Total_Reports = (source_obj.Total_Reports or 0) + 1
            source_obj.Total_Claims = (source_obj.Total_Claims or 0) + 1
            source_obj.Trust_Score = round(((source_obj.Total_Reports - (source_obj.Fake_Reports or 0)) / max(1, source_obj.Total_Reports)) * 100.0, 1)
            source_obj.Last_Seen = datetime.utcnow()

        if portal_src and db:
            portal_src.Total_Reports = (portal_src.Total_Reports or 0) + 1
            portal_src.Total_Claims = (portal_src.Total_Claims or 0) + 1
            portal_src.Trust_Score = round(((portal_src.Total_Reports - (portal_src.Fake_Reports or 0)) / max(1, portal_src.Total_Reports)) * 100.0, 1)
            portal_src.Last_Seen = datetime.utcnow()
        if db:
            db.commit()

    else:  # score_sum < 27
        verdict_status = "Fake"
        verdict_summary = "UNVERIFIED / FALSE REPORT: Contradicted by meteorological observations and lacking corroboration (Score < 27)."
        
        # Source penalty (Metrics live on Source)
        if source_obj and db:
            source_obj.Total_Reports = (source_obj.Total_Reports or 0) + 1
            source_obj.Fake_Reports = (source_obj.Fake_Reports or 0) + 1
            source_obj.Warnings_Count = (source_obj.Warnings_Count or 0) + 1
            source_obj.Total_Claims = (source_obj.Total_Claims or 0) + 1
            source_obj.False_Claims = (source_obj.False_Claims or 0) + 1
            source_obj.Trust_Score = round(((source_obj.Total_Reports - source_obj.Fake_Reports) / max(1, source_obj.Total_Reports)) * 100.0, 1)
            source_obj.Last_Seen = datetime.utcnow()

            if source_obj.Warnings_Count >= 3 or source_obj.Trust_Status == "RED":
                source_obj.Trust_Status = "RED"
            elif source_obj.Trust_Status == "GREEN":
                source_obj.Trust_Status = "GREY"
            else:
                source_obj.Trust_Status = "GREY"

        if not is_external_report and portal_src and db:
            portal_src.Total_Reports = (portal_src.Total_Reports or 0) + 1
            portal_src.Fake_Reports = (portal_src.Fake_Reports or 0) + 1
            portal_src.Total_Claims = (portal_src.Total_Claims or 0) + 1
            portal_src.False_Claims = (portal_src.False_Claims or 0) + 1
            portal_src.Trust_Score = round(((portal_src.Total_Reports - portal_src.Fake_Reports) / max(1, portal_src.Total_Reports)) * 100.0, 1)
            portal_src.Last_Seen = datetime.utcnow()
            if portal_src.Fake_Reports >= 3:
                portal_src.Trust_Status = "RED"
        elif is_external_report and portal_src and db:
            portal_src.Total_Reports = (portal_src.Total_Reports or 0) + 1
            portal_src.Total_Claims = (portal_src.Total_Claims or 0) + 1
            portal_src.Last_Seen = datetime.utcnow()
        if db:
            db.commit()

    # Save to DB
    saved_report_id = _save_report_to_db(
        db=db, user_id=user_id, source_id=source_id, report_text=report_text,
        incident_time=incident_time, city=city_clean, state=state_clean, lat=latitude, lon=longitude,
        event_type=event_type, media_url=media_url, score=float(score_sum),
        status=verdict_status, breakdown=breakdown, is_ai=0,
        forensics=forensics_info,
    )

    result_payload = {
        "report_id": saved_report_id,
        "city": city_clean,
        "state": state_clean,
        "latitude": latitude,
        "longitude": longitude,
        "event_type": event_type,
        "verification_status": verdict_status,
        "verification_score": float(score_sum),
        "hint_breakdown": breakdown,
        "is_ai_generated": False,
        "ai_confidence": ai_score,
        "ai_reason": forensics_info.get("ai_reason") if forensics_info else None,
        "user_trust_status": portal_src.Trust_Status if portal_src else (source_obj.Trust_Status if source_obj else "GREY"),
        "trust_status": portal_src.Trust_Status if portal_src else (source_obj.Trust_Status if source_obj else "GREY"),
        "source_trust_score": portal_src.Trust_Score if portal_src else (source_obj.Trust_Score if source_obj else 50.0),
        "verdict_summary": verdict_summary,
        "from_cache": False,
        "from_database": False,
    }

    # Cache result
    cache_incident_result(cache_lookup_key, result_payload)
    return result_payload


def _save_report_to_db(
    db, user_id, source_id, report_text, incident_time, city, state, lat, lon,
    event_type, media_url, score, status, breakdown, is_ai, forensics
) -> Optional[int]:
    """Helper to persist report and media records to database."""
    if not db:
        return None
    try:
        from app.services.image_forensics import parse_datetime_flexible
        inc_dt = parse_datetime_flexible(incident_time) if incident_time else datetime.utcnow()
        report_record = Reports(
            User_Id=user_id,
            Source_Id=source_id,
            Report=report_text,
            Time=datetime.utcnow(),
            Incident_Time=inc_dt,
            City=city,
            State=state,
            Latitude=lat,
            Longitude=lon,
            Event_Type=event_type,
            Img_Vid_Url=media_url,
            Verification_Score=score,
            Verification_Status=status,
            Hint_Breakdown=json.dumps(breakdown),
            Is_AI_Generated=is_ai,
        )
        db.add(report_record)
        db.flush()

        if forensics:
            img_record = Images_Videos(
                Report_Id=report_record.Id,
                Img_Hash=forensics.get("img_hash", "0000000000000000"),
                Exif_GPS=forensics.get("exif_gps"),
                Exif_Timestamp=forensics.get("exif_timestamp"),
                Exif_Camera=forensics.get("exif_camera"),
                Is_AI_Generated=1 if forensics.get("is_ai_generated") else 0,
                AI_Score=float(forensics.get("ai_score", 0.0)),
            )
            db.add(img_record)

        db.commit()
        return report_record.Id
    except Exception as e:
        logger.error(f"Error saving report to DB: {e}")
        db.rollback()
        return None

