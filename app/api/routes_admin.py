"""
Admin & Reviewer Control Room Endpoints.

Provides:
- Pending Review Queue for ambiguous incidents (35 <= sum < 75)
- Review action dispatch (Approve / Reject / On Hold) with audit logs
- User moderation console (Green Verified, Grey Warned, Red Blocked lists)
- Ingestion pipeline triggers & system telemetry
"""
import json
import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc

logger = logging.getLogger(__name__)

from app.api.deps import get_db, require_admin
from app.models.admin import Admin
from app.models.Reports import Reports
from app.models.user import User
from app.models.Actions_log import Action_Log
from app.models.sources import Source
from app.services.cache_service import add_highlighted_event, cache_incident_result
from app.ingestion.imd_collector import IMDCollector
from app.ingestion.gnews_collector import GNewsCollector
from app.ingestion.newsdata_collector import NewsDataCollector
from app.services.verification_engine import process_and_verify_incident

router = APIRouter()


class ReviewActionRequest(BaseModel):
    action: Optional[str] = Field(
        None,
        description="Review decision action: 'Approved' / 'Authentic', 'Rejected' / 'Fake', or 'On hold' / 'Underprocess'",
        example="Approved",
    )
    verification_status: Optional[str] = Field(
        None,
        description="Direct verification status: 'Othentic' / 'Authentic', 'Fake', or 'Underprocess'",
        example="Othentic",
    )
    status: Optional[str] = Field(
        None,
        description="Alias for verification status or action",
        example="Authentic",
    )
    comment: Optional[str] = Field(
        None,
        description="Reviewer / Administrator comment or explanation note",
        example="Report confirmed authentic after satellite and ground telemetry review.",
    )
    verification_score: Optional[float] = Field(
        None,
        description="Optional truth/verification score override (0-100)",
        example=85.0,
    )
    report_text: Optional[str] = Field(
        None,
        description="Optional updated or corrected incident report description text",
    )
    event_type: Optional[str] = Field(
        None,
        description="Optional updated disaster event type (e.g. flooding, thunderstorm)",
    )
    city: Optional[str] = Field(
        None,
        description="Optional updated city name",
    )
    state: Optional[str] = Field(
        None,
        description="Optional updated state name",
    )


class UserStatusUpdateRequest(BaseModel):
    trust_status: Optional[str] = None  # "GREEN", "GREY", "RED"
    is_active: Optional[bool] = None


@router.get("/pending-review")
def get_pending_review_queue(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
):
    """
    Returns all reports in 'Underprocess' state requiring human auditor / admin review.
    """
    pending = db.query(Reports).filter(
        Reports.Verification_Status == "Underprocess"
    ).order_by(desc(Reports.Time)).limit(limit).all()

    items = []
    for r in pending:
        breakdown = []
        if r.Hint_Breakdown:
            try:
                breakdown = json.loads(r.Hint_Breakdown)
            except Exception:
                pass

        user_info = None
        if r.user:
            src = db.query(Source).filter(
                Source.Username == r.user.Email,
                Source.Platform == "CitizenPortal"
            ).first()
            user_info = {
                "id": r.user.Id,
                "name": r.user.Name,
                "email": r.user.Email,
                "trust_status": src.Trust_Status if src else "GREY",
            }

        latest_log = r.action_logs[-1] if r.action_logs else None
        admin_comment = r.Admin_Comment or (latest_log.Comment if latest_log else None)
        reviewed_by = r.Reviewed_By or (latest_log.admin.Name if latest_log and latest_log.admin else None)
        review_action = r.Review_Action or (latest_log.Action if latest_log else None)
        reviewed_at = r.Reviewed_at.isoformat() if r.Reviewed_at else (latest_log.Review_at.isoformat() if latest_log else None)

        items.append({
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
            "hint_breakdown": breakdown,
            "user": user_info,
            "timestamp": r.Time.isoformat() if r.Time else None,
        })

    return {
        "pending_count": len(items),
        "queue": items,
    }


@router.post("/review/{report_id}")
def submit_admin_review(
    report_id: int,
    payload: ReviewActionRequest,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
):
    """
    Reviewer submits decision on an ambiguous incident.
    - Approved -> Marks as 'Othentic', updates 7-day highlight cache, promotes user.
    - Rejected -> Marks as 'Fake', updates cache, applies user penalties.
    - On hold -> Stays in 'Underprocess' with audit note.
    """
    report = db.query(Reports).filter(Reports.Id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    raw_decision = (payload.action or payload.verification_status or payload.status or "Approved").strip()
    decision_lower = raw_decision.lower().replace("_", " ").replace("-", " ")

    if decision_lower in ["approved", "approve", "authentic", "othentic", "verified", "true", "valid"]:
        action_clean = "Approved"
        status_clean = "Othentic"
        score_clean = payload.verification_score if payload.verification_score is not None else max(report.Verification_Score, 85.0)
    elif decision_lower in ["rejected", "reject", "fake", "disinformation", "false", "invalid"]:
        action_clean = "Rejected"
        status_clean = "Fake"
        score_clean = payload.verification_score if payload.verification_score is not None else min(report.Verification_Score, 25.0)
    elif decision_lower in ["on hold", "hold", "underprocess", "pending", "review"]:
        action_clean = "On hold"
        status_clean = "Underprocess"
        score_clean = payload.verification_score if payload.verification_score is not None else report.Verification_Score
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action or status: '{raw_decision}'. Allowed values: Approved/Authentic, Rejected/Fake, or On hold/Underprocess.",
        )

    # 1. Update Reports table status and score
    report.Verification_Status = status_clean
    report.Verification_Score = score_clean

    # 2. Update optional report content fields if provided
    if payload.report_text is not None and payload.report_text.strip():
        report.Report = payload.report_text.strip()
    if payload.event_type is not None and payload.event_type.strip():
        report.Event_Type = payload.event_type.strip()
    if payload.city is not None and payload.city.strip():
        report.City = payload.city.strip()
    if payload.state is not None and payload.state.strip():
        report.State = payload.state.strip()

    # 3. Store Reviewer Audit Comment directly on the report
    comment_text = (payload.comment or "").strip() or f"Reviewed as {action_clean} by {admin.Name}."
    report.Admin_Comment = comment_text
    report.Reviewed_By = admin.Name
    report.Review_Action = action_clean
    report.Reviewed_at = datetime.utcnow()

    # 4. Handle trust score accounting and live cache updates
    if action_clean == "Approved":
        # Update 7-Day Highlighted Cache
        add_highlighted_event(report.City, {
            "city": report.City,
            "state": report.State,
            "latitude": report.Latitude,
            "longitude": report.Longitude,
            "event_type": report.Event_Type,
            "description": report.Report,
            "verification_score": report.Verification_Score,
            "status": "Othentic",
            "timestamp": datetime.utcnow().isoformat(),
        })
        target_src = report.source
        if not target_src and report.user:
            target_src = db.query(Source).filter(
                Source.Username == report.user.Email,
                Source.Platform == "CitizenPortal"
            ).first()
            if not target_src:
                target_src = Source(
                    Username=report.user.Email,
                    Source_Name=report.user.Name or report.user.Email,
                    Platform="CitizenPortal",
                    Trust_Status="GREEN",
                    Total_Reports=1,
                    Fake_Reports=0,
                    Warnings_Count=0,
                    Total_Claims=1,
                    True_Claims=1,
                    False_Claims=0,
                    Trust_Score=100.0,
                )
                db.add(target_src)
                db.flush()
        if target_src:
            target_src.Trust_Status = "GREEN"
            target_src.True_Claims = (target_src.True_Claims or 0) + 1
            target_src.Total_Claims = (target_src.Total_Claims or 0) + 1
            target_src.Trust_Score = round((target_src.True_Claims / max(1, target_src.Total_Claims)) * 100.0, 1)

    elif action_clean == "Rejected":
        target_src = report.source
        if not target_src and report.user:
            target_src = db.query(Source).filter(
                Source.Username == report.user.Email,
                Source.Platform == "CitizenPortal"
            ).first()
            if not target_src:
                target_src = Source(
                    Username=report.user.Email,
                    Source_Name=report.user.Name or report.user.Email,
                    Platform="CitizenPortal",
                    Trust_Status="GREY",
                    Total_Reports=1,
                    Fake_Reports=1,
                    Warnings_Count=1,
                    Total_Claims=1,
                    True_Claims=0,
                    False_Claims=1,
                    Trust_Score=0.0,
                )
                db.add(target_src)
                db.flush()
        if target_src:
            target_src.Fake_Reports = (target_src.Fake_Reports or 0) + 1
            target_src.False_Claims = (target_src.False_Claims or 0) + 1
            target_src.Total_Claims = (target_src.Total_Claims or 0) + 1
            target_src.Warnings_Count = (target_src.Warnings_Count or 0) + 1
            if target_src.Warnings_Count >= 3:
                target_src.Trust_Status = "RED"
            else:
                target_src.Trust_Status = "GREY"
            target_src.Trust_Score = round((target_src.True_Claims / max(1, target_src.Total_Claims)) * 100.0, 1)

    # 5. Create Audit Log Entry
    log_entry = Action_Log(
        Admin_Id=admin.Id,
        Report_Id=report.Id,
        Action=action_clean,
        Comment=comment_text,
        Review_at=datetime.utcnow(),
    )
    db.add(log_entry)
    db.commit()
    db.refresh(report)

    return {
        "status": "success",
        "message": f"Report #{report.Id} reviewed and marked as '{report.Verification_Status}' by {admin.Name}.",
        "updated_status": report.Verification_Status,
        "report": {
            "id": report.Id,
            "report_text": report.Report,
            "city": report.City,
            "state": report.State,
            "event_type": report.Event_Type,
            "verification_score": report.Verification_Score,
            "verification_status": report.Verification_Status,
            "admin_comment": report.Admin_Comment,
            "reviewed_by": report.Reviewed_By,
            "review_action": report.Review_Action,
            "reviewed_at": report.Reviewed_at.isoformat() if report.Reviewed_at else None,
        },
    }


@router.get("/users")
def get_user_moderation_list(
    status_filter: Optional[str] = Query(None, description="GREEN, GREY, or RED"),
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
):
    """
    Returns users categorized into Green (Verified), Grey (Monitoring/Warned), and Red (Blocked) lists.
    Trust status and report metrics are resolved from the Sources table.
    """
    users = db.query(User).order_by(desc(User.Created_at)).all()
    data = []
    for u in users:
        src = db.query(Source).filter(
            Source.Username == u.Email,
            Source.Platform == "CitizenPortal"
        ).first()
        t_status = src.Trust_Status if src else "GREY"
        if status_filter and status_filter.upper() in ["GREEN", "GREY", "RED"]:
            if t_status != status_filter.upper():
                continue

        data.append({
            "id": u.Id,
            "name": u.Name,
            "email": u.Email,
            "location": u.Location,
            "trust_status": t_status,
            "is_active": u.Is_Active,
            "total_reports": src.Total_Reports if src else 0,
            "fake_reports": src.Fake_Reports if src else 0,
            "warnings_count": src.Warnings_Count if src else 0,
            "created_at": u.Created_at.isoformat() if u.Created_at else None,
        })

    return {
        "total_users": len(data),
        "users": data,
    }


@router.post("/users/{user_id}/status")
def update_user_status(
    user_id: int,
    payload: UserStatusUpdateRequest,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
):
    """
    Admin updates a user's trust category (e.g. unblock, whitelist as Green, or ban to Red).
    Updates the CitizenPortal entry in Sources and User account activity.
    """
    user = db.query(User).filter(User.Id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    src = db.query(Source).filter(
        Source.Username == user.Email,
        Source.Platform == "CitizenPortal"
    ).first()
    if not src:
        src = Source(
            Username=user.Email,
            Source_Name=user.Name or user.Email,
            Platform="CitizenPortal",
            Trust_Status="GREY",
            Total_Reports=0,
            Fake_Reports=0,
            Warnings_Count=0,
            Total_Claims=0,
            True_Claims=0,
            False_Claims=0,
            Trust_Score=50.0,
        )
        db.add(src)
        db.flush()

    if payload.trust_status:
        ts = payload.trust_status.upper()
        if ts in ["GREEN", "GREY", "RED"]:
            src.Trust_Status = ts
            if ts == "RED":
                user.Is_Active = False
            elif ts in ["GREEN", "GREY"] and not user.Is_Active:
                user.Is_Active = True

    if payload.is_active is not None:
        user.Is_Active = payload.is_active

    db.commit()
    return {
        "status": "success",
        "message": f"User #{user.Id} status updated: Trust={src.Trust_Status}, Active={user.Is_Active}",
    }


@router.post("/trigger-ingestion")
def trigger_ingestion_cycle(
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
):
    """
    Triggers an immediate multi-source collection run (IMD, GNews, NewsData)
    and processes all incoming events through the truth scoring engine.
    """
    imd = IMDCollector()
    gnews = GNewsCollector()
    newsdata = NewsDataCollector()

    collected_events = []
    try:
        collected_events.extend(imd.fetch())
    except Exception as e:
        logger.warning(f"IMD run error: {e}")

    try:
        collected_events.extend(gnews.fetch())
    except Exception as e:
        logger.warning(f"GNews run error: {e}")

    try:
        collected_events.extend(newsdata.fetch())
    except Exception as e:
        logger.warning(f"NewsData run error: {e}")

    processed_count = 0
    for ev in collected_events:
        try:
            process_and_verify_incident(
                report_text=ev.get("raw_text", ""),
                city=ev.get("city") or "Delhi",
                state=ev.get("state"),
                latitude=ev.get("latitude") or 28.6139,
                longitude=ev.get("longitude") or 77.2090,
                event_type=ev.get("event_type_guess"),
                media_url=ev.get("media_urls", [None])[0] if ev.get("media_urls") else None,
                source_id=2,
                db=db,
            )
            processed_count += 1
        except Exception:
            pass

    return {
        "status": "success",
        "collected_events_count": len(collected_events),
        "verified_and_stored_count": processed_count,
        "message": "Ingestion cycle completed successfully.",
    }


@router.get("/system-telemetry")
def get_system_telemetry(admin: Admin = Depends(require_admin)):
    """
    Returns live system telemetry: ML model status, API configurations, and cache status.
    """
    from app.ml.trained_model import _models_loaded
    from app.services.cache_service import _redis_available

    return {
        "status": "operational",
        "ml_models_loaded": _models_loaded,
        "redis_connected": _redis_available(),
        "timestamp": datetime.utcnow().isoformat(),
        "active_sources": [
            {"source": "IMD Official Alerts", "status": "active"},
            {"source": "Windy Atmospheric Engine", "status": "active"},
            {"source": "OpenWeatherMap Telemetry", "status": "active"},
            {"source": "GNews Ingestion Stream", "status": "active"},
            {"source": "NewsData.io Feeds", "status": "active"},
            {"source": "Citizen Reporting Portal", "status": "active"},
        ]
    }
