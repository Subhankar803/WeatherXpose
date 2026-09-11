"""
Citizen Weather Report Submission & Instant Verification Endpoint.
"""
import os
import shutil
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Form, File, UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.verification_engine import process_and_verify_incident
from app.ml.trained_model import CITY_COORDS

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("")
@router.post("/")
async def submit_citizen_report(
    report_text: str = Form(..., description="Description or user query about the weather incident (e.g., 'Is there flooding in Dadar?')"),
    city: str = Form(..., description="City or District name in India"),
    state: Optional[str] = Form(None, description="State name"),
    latitude: Optional[float] = Form(None, description="GPS Latitude"),
    longitude: Optional[float] = Form(None, description="GPS Longitude"),
    event_type: Optional[str] = Form(None, description="Event type: flooding, rainfall, thunderstorm, heatwave, etc."),
    incident_time: Optional[str] = Form(None, description="Reported date/time of incident (e.g. '2026-09-08 14:30')"),
    platform: Optional[str] = Form("Citizen", description="Source platform name: Instagram, Twitter, Facebook, Citizen, Telegram, Reddit, etc."),
    source_username: Optional[str] = Form(None, description="Username/Handle from where the image/video was obtained (e.g. 'Pritam Haldar')"),
    media_file: Optional[UploadFile] = File(None, description="Optional photo or video of incident"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Submits a citizen report with image/video forensics, metadata timestamp validation,
    social source trust accounting, and multi-signal truth scoring.
    """
    if current_user and not current_user.Is_Active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated by an administrator.",
        )

    # Auto-resolve coordinates from city name if omitted
    if latitude is None or longitude is None:
        coords = CITY_COORDS.get(city.title())
        if coords:
            latitude, longitude = coords
        else:
            latitude, longitude = 20.5937, 78.9629  # Center of India fallback

    # Auto-resolve state from city or coordinates if omitted or generic
    from app.utils.geo_utils import resolve_state_for_city_or_coords
    if not state or state.strip().lower() in ["india", "unknown", "none", ""]:
        state = resolve_state_for_city_or_coords(city, float(latitude), float(longitude))

    media_bytes = None
    media_url = None
    orig_filename = None

    if media_file and getattr(media_file, "filename", None):
        try:
            raw_bytes = await media_file.read()
            if len(raw_bytes) > 0:
                orig_filename = media_file.filename
                media_bytes = raw_bytes
                # Save file locally
                filename = f"report_{int(datetime.utcnow().timestamp())}_{orig_filename}"
                filepath = os.path.join(UPLOAD_DIR, filename)
                with open(filepath, "wb") as f:
                    f.write(media_bytes)
                media_url = f"/uploads/{filename}"
        except Exception as e:
            logger.warning(f"Error saving uploaded file: {e}")

    # Run full verification pipeline
    user_id = current_user.Id if current_user else None
    result = process_and_verify_incident(
        report_text=report_text,
        city=city,
        state=state,
        latitude=float(latitude),
        longitude=float(longitude),
        event_type=event_type,
        incident_time=incident_time,
        platform=platform,
        source_username=source_username or (current_user.Name if current_user else "anonymous"),
        media_bytes=media_bytes,
        media_url=media_url,
        filename=orig_filename,
        user_id=user_id,
        source_id=None,
        is_citizen_submission=True,
        db=db,
    )

    return {
        "status": "success",
        "message": "Weather report processed and analyzed successfully.",
        "data": result,
    }


@router.get("/chat-query")
def normal_condition_chat_query(
    query: str,
    city: str,
    state: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Normal dashboard mode (when user has not attached an image/video):
    Simple chat bar to query weather conditions and active alerts for any location.
    """
    lat, lon = CITY_COORDS.get(city.title(), (20.5937, 78.9629))
    from app.utils.geo_utils import resolve_state_for_city_or_coords
    if not state or state.strip().lower() in ["india", "unknown", "none", ""]:
        state = resolve_state_for_city_or_coords(city, lat, lon)
    result = process_and_verify_incident(
        report_text=query,
        city=city,
        state=state,
        latitude=lat,
        longitude=lon,
        platform="DashboardChat",
        source_username="citizen_query",
        db=db,
    )
    return {
        "status": "success",
        "mode": "chat_query",
        "query": query,
        "city": city,
        "result": result,
    }

