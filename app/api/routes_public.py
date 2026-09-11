"""
Public Big Data Analytics & Weather Intelligence Endpoints.

Provides:
- Date-wise, Event-wise, Location-wise, and Verification Status filtering for reports
- Live map incidents feed with GPS coordinates for Leaflet
- Big Data real-time metrics & KPI summary
- Tier 1 live weather grid (5-10m cache)
- Tier 2 active 7-day weather incidents feed
- Direct ML fusion evaluation for Indian cities
"""
import json
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.api.deps import get_db
from app.models import Reports, Images_Videos, Source
from app.services.cache_service import (
    get_all_cached_weather_grid,
    get_location_weather,
    set_location_weather,
    get_all_active_7day_events,
    get_city_active_7day_events,
)
from app.ingestion.openweather_collector import get_city_current_weather
from app.ingestion.imd_collector import IMDCollector
from app.ml.trained_model import evaluate_city_fusion, CITY_COORDS, CITY_FLOOD_PROFILE

router = APIRouter()
imd_collector = IMDCollector()


class CityEvaluateRequest(BaseModel):
    cities: Optional[List[str]] = None


@router.get("/reports")
def get_filtered_reports(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    event_type: Optional[str] = Query(None, description="Event filter (flooding, rainfall, thunderstorm, heatwave, etc.)"),
    city: Optional[str] = Query(None, description="City / District filter"),
    state: Optional[str] = Query(None, description="State filter"),
    status: Optional[str] = Query(None, description="Verification status: Othentic, Underprocess, Fake"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Query and filter collected reports date-wise, event-wise, location-wise, and status-wise.
    """
    query = db.query(Reports)

    if start_date:
        try:
            sd = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Reports.Time >= sd)
        except ValueError:
            pass

    if end_date:
        try:
            ed = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(Reports.Time < ed)
        except ValueError:
            pass

    if event_type and event_type.lower() != "all":
        query = query.filter(Reports.Event_Type.ilike(f"%{event_type}%"))

    if city:
        query = query.filter(Reports.City.ilike(f"%{city}%"))

    if state:
        query = query.filter(Reports.State.ilike(f"%{state}%"))

    if status and status.lower() != "all":
        # Handle spelling flexibility (Othentic / Authentic)
        status_target = "Othentic" if status.lower() in ["authentic", "othentic", "verified"] else status.capitalize()
        query = query.filter(Reports.Verification_Status == status_target)

    total_count = query.count()
    records = query.order_by(desc(Reports.Time)).offset(offset).limit(limit).all()

    formatted = []
    for r in records:
        breakdown_data = []
        if r.Hint_Breakdown:
            try:
                breakdown_data = json.loads(r.Hint_Breakdown)
            except Exception:
                pass

        latest_log = r.action_logs[-1] if r.action_logs else None
        admin_comment = r.Admin_Comment or (latest_log.Comment if latest_log else None)
        reviewed_by = r.Reviewed_By or (latest_log.admin.Name if latest_log and latest_log.admin else None)
        review_action = r.Review_Action or (latest_log.Action if latest_log else None)
        reviewed_at = r.Reviewed_at.isoformat() if r.Reviewed_at else (latest_log.Review_at.isoformat() if latest_log else None)

        formatted.append({
            "id": r.Id,
            "report_text": r.Report,
            "city": r.City,
            "state": r.State,
            "latitude": r.Latitude,
            "longitude": r.Longitude,
            "event_type": r.Event_Type,
            "media_url": r.Img_Vid_Url,
            "verification_score": r.Verification_Score,
            "verification_status": r.Verification_Status,
            "admin_comment": admin_comment,
            "reviewed_by": reviewed_by,
            "review_action": review_action,
            "reviewed_at": reviewed_at,
            "action_logs": [
                {
                    "id": log.Id,
                    "admin_id": log.Admin_Id,
                    "admin_name": log.admin.Name if log.admin else None,
                    "action": log.Action,
                    "comment": log.Comment,
                    "reviewed_at": log.Review_at.isoformat() if log.Review_at else None,
                }
                for log in r.action_logs
            ] if r.action_logs else [],
            "is_ai_generated": bool(r.Is_AI_Generated),
            "hint_breakdown": breakdown_data,
            "timestamp": r.Time.isoformat() if r.Time else None,
        })

    return {
        "total_records": total_count,
        "returned": len(formatted),
        "limit": limit,
        "offset": offset,
        "data": formatted,
    }


@router.get("/reports/{report_id}")
def get_report_by_id(report_id: int, db: Session = Depends(get_db)):
    """
    Fetches a specific weather incident report by its ID, including verification status,
    admin review comments, and complete action log audit trail.
    """
    r = db.query(Reports).filter(Reports.Id == report_id).first()
    if not r:
        raise HTTPException(status_code=404, detail=f"Report #{report_id} not found")

    breakdown_data = []
    if r.Hint_Breakdown:
        try:
            breakdown_data = json.loads(r.Hint_Breakdown)
        except Exception:
            pass

    latest_log = r.action_logs[-1] if r.action_logs else None
    admin_comment = r.Admin_Comment or (latest_log.Comment if latest_log else None)
    reviewed_by = r.Reviewed_By or (latest_log.admin.Name if latest_log and latest_log.admin else None)
    review_action = r.Review_Action or (latest_log.Action if latest_log else None)
    reviewed_at = r.Reviewed_at.isoformat() if r.Reviewed_at else (latest_log.Review_at.isoformat() if latest_log else None)

    return {
        "status": "success",
        "data": {
            "id": r.Id,
            "report_text": r.Report,
            "city": r.City,
            "state": r.State,
            "latitude": r.Latitude,
            "longitude": r.Longitude,
            "event_type": r.Event_Type,
            "media_url": r.Img_Vid_Url,
            "verification_score": r.Verification_Score,
            "verification_status": r.Verification_Status,
            "admin_comment": admin_comment,
            "reviewed_by": reviewed_by,
            "review_action": review_action,
            "reviewed_at": reviewed_at,
            "action_logs": [
                {
                    "id": log.Id,
                    "admin_id": log.Admin_Id,
                    "admin_name": log.admin.Name if log.admin else None,
                    "action": log.Action,
                    "comment": log.Comment,
                    "reviewed_at": log.Review_at.isoformat() if log.Review_at else None,
                }
                for log in r.action_logs
            ] if r.action_logs else [],
            "is_ai_generated": bool(r.Is_AI_Generated),
            "hint_breakdown": breakdown_data,
            "timestamp": r.Time.isoformat() if r.Time else None,
        }
    }


@router.get("/map/active-incidents")
def get_map_active_incidents(db: Session = Depends(get_db)):
    """
    Returns active verified and under-review incidents with coordinates for Leaflet map markers.
    """
    incidents = db.query(Reports).filter(
        Reports.Verification_Status.in_(["Othentic", "Underprocess"])
    ).order_by(desc(Reports.Time)).limit(100).all()

    features = []
    for inc in incidents:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [inc.Longitude, inc.Latitude],
            },
            "properties": {
                "id": inc.Id,
                "city": inc.City,
                "state": inc.State,
                "event_type": inc.Event_Type,
                "report": inc.Report,
                "verification_score": inc.Verification_Score,
                "verification_status": inc.Verification_Status,
                "media_url": inc.Img_Vid_Url,
                "timestamp": inc.Time.isoformat() if inc.Time else None,
            }
        })

    return {
        "type": "FeatureCollection",
        "total_incidents": len(features),
        "features": features,
    }


@router.get("/stats/dashboard")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Big Data aggregated platform metrics:
    - Total claims processed
    - Verified (Authentic) vs Disinformation (Fake) ratio
    - Pending reviewer queue count
    - Total AI-generated deepfake images detected & neutralized
    - Event category distribution
    - Top affected Indian cities
    """
    total_claims = db.query(func.count(Reports.Id)).scalar() or 0
    verified_count = db.query(func.count(Reports.Id)).filter(Reports.Verification_Status == "Othentic").scalar() or 0
    fake_count = db.query(func.count(Reports.Id)).filter(Reports.Verification_Status == "Fake").scalar() or 0
    pending_count = db.query(func.count(Reports.Id)).filter(Reports.Verification_Status == "Underprocess").scalar() or 0
    ai_fakes_count = db.query(func.count(Reports.Id)).filter(Reports.Is_AI_Generated == 1).scalar() or 0

    # Event distribution
    event_distribution = {}
    event_counts = db.query(Reports.Event_Type, func.count(Reports.Id)).group_by(Reports.Event_Type).all()
    for ev, c in event_counts:
        if ev:
            event_distribution[ev] = c

    # Top affected cities
    top_cities = []
    city_counts = db.query(Reports.City, func.count(Reports.Id)).filter(
        Reports.Verification_Status == "Othentic"
    ).group_by(Reports.City).order_by(desc(func.count(Reports.Id))).limit(6).all()
    for c_name, c_cnt in city_counts:
        top_cities.append({"city": c_name, "verified_incidents": c_cnt})

    authenticity_rate = round((verified_count / total_claims * 100), 1) if total_claims > 0 else 100.0

    return {
        "total_claims_processed": total_claims,
        "verified_authentic_claims": verified_count,
        "disinformation_fake_claims": fake_count,
        "pending_review_queue": pending_count,
        "ai_fakes_detected": ai_fakes_count,
        "platform_authenticity_rate": authenticity_rate,
        "event_distribution": event_distribution,
        "top_affected_cities": top_cities,
    }


@router.get("/weather/live-grid")
def get_live_weather_grid():
    """
    Tier 1 Cache: Returns live weather telemetry grid across Indian cities (refreshed every 5-10m).
    """
    grid = get_all_cached_weather_grid()
    if not grid:
        # Populate major hubs
        major_cities = ["Mumbai", "Delhi", "Kolkata", "Chennai", "Bengaluru", "Hyderabad", "Guwahati", "Jaipur"]
        for c in major_cities:
            data = get_city_current_weather(c)
            set_location_weather(c, data)
        grid = get_all_cached_weather_grid()

    return {
        "status": "success",
        "tier": "Tier 1 Cache (5-10m refresh)",
        "total_stations": len(grid),
        "data": grid,
    }


@router.get("/weather/imd-alerts")
def get_live_imd_alerts():
    """
    Returns live official IMD district alerts across India directly from the official IMD Nowcast feed.
    """
    alerts = imd_collector.fetch_live_alerts()
    return {
        "status": "success",
        "source": "India Meteorological Department (Official)",
        "feed_url": "https://mausam.imd.gov.in/imd_latest/contents/dist_nowcast_rss.php",
        "total_active_alerts": len(alerts),
        "alerts": alerts,
    }


@router.get("/weather/imd-warning/{city}")
def get_city_imd_warning(city: str):
    """
    Queries official IMD bulletin and warning status for a specific city or district.
    """
    warning = imd_collector.get_district_warning(city)
    return {
        "status": "success",
        "city": city,
        "warning": warning,
    }


@router.get("/events/7day-active")
def get_active_7day_events():
    """
    Tier 2 Cache: Returns active highlighted weather incidents retained within the 7-day lifecycle.
    """
    events = get_all_active_7day_events()
    return {
        "status": "success",
        "tier": "Tier 2 Cache (7-Day Retention Window)",
        "active_events_count": len(events),
        "events": events,
    }


@router.get("/cities")
def get_supported_cities():
    return {
        "supported_cities": sorted(CITY_COORDS.keys()),
        "coordinates": CITY_COORDS,
    }


@router.get("/evaluate/{city}")
def evaluate_single_city(city: str):
    """
    Evaluates ML models for a single city using live atmospheric & environmental inputs.
    """
    city_title = city.strip().title()
    weather = get_city_current_weather(city_title)
    fusion_result = evaluate_city_fusion(
        city=city_title,
        temp_c=weather.get("temperature", 28.0),
        precip_mm=weather.get("precipitation_mm", 0.0),
        wind_kmh=weather.get("wind_speed_kmh", 15.0),
    )
    return {
        "city": city_title,
        "live_telemetry": weather,
        "ml_inference": fusion_result,
    }


@router.post("/evaluate")
def evaluate_multiple_cities(payload: CityEvaluateRequest):
    """
    Evaluates ML models for a batch of cities.
    """
    cities = payload.cities or ["Mumbai", "Delhi", "Chennai", "Kolkata", "Bengaluru"]
    results = []
    for c in cities:
        try:
            weather = get_city_current_weather(c)
            res = evaluate_city_fusion(
                city=c,
                temp_c=weather.get("temperature", 28.0),
                precip_mm=weather.get("precipitation_mm", 0.0),
                wind_kmh=weather.get("wind_speed_kmh", 15.0),
            )
            results.append({"city": c, "telemetry": weather, "inference": res})
        except Exception as e:
            results.append({"city": c, "error": str(e)})

    return {
        "status": "success",
        "processed_count": len(results),
        "data": results,
    }
