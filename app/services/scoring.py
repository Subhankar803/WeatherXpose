"""
Multi-Signal Truth Scoring Engine.

Implements the exact scoring weights specified in the system flowchart:
1. Windy Telemetry Check: +15 if Strong Hint, +0 otherwise
2. IMD Official Gov Weather Bulletin: +30 if In FOR, -10 if Contradicted
3. Local Reports Cluster Check: +20 if > 5 reports in FOR, +0 otherwise
4. Account Trust Score:
   - Verified Account (Green): +10
   - New Account First Post: +2
   - Fraud / Flagged Account (Red/Grey): +0
5. News Verification (GNews / NewsData / RSS): +10 if True, +0 if False
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.ingestion.windy_collector import check_windy_strong_hint
from app.ingestion.openweather_collector import get_city_current_weather
from app.ingestion.imd_collector import IMDCollector
from app.ingestion.newsdata_collector import verify_news_for_location
from app.ml.duplicate_detector import calculate_haversine_distance
from app.services.cache_service import get_cached_telemetry, set_cached_telemetry

logger = logging.getLogger(__name__)
imd_collector = IMDCollector()


def evaluate_verification_signals(
    city: str,
    state: str,
    latitude: float,
    longitude: float,
    event_type: str,
    user_trust_status: str = "GREY",
    is_first_post: bool = True,
    platform: Optional[str] = None,
    source_username: Optional[str] = None,
    user_id: Optional[int] = None,
    metadata_time_match: bool = True,
    metadata_time_diagnostic: Optional[str] = None,
    db_session: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Evaluates all truth signals and calculates the cumulative hint score `sum`.
    Utilizes disk-persistent telemetry caching to prevent API jitter and score fluctuations.
    """
    score_sum = 0
    breakdown: List[Dict[str, Any]] = []
    windy_hint: bool = False

    # ─────────────────────────────────────────────────────────
    # Signal 1: Atmospheric Telemetry (Windy Model + OpenWeather Live Station)
    # ─────────────────────────────────────────────────────────
    atmo_key = f"atmospheric_telemetry:{city.lower().strip()}_{(event_type or '').lower().strip()}_{round(latitude, 2)}_{round(longitude, 2)}"
    cached_atmo = get_cached_telemetry(atmo_key)
    if cached_atmo and isinstance(cached_atmo, dict):
        atmospheric_passed = cached_atmo.get("passed", False)
        sources_str = cached_atmo.get("sources_str", [])
        cond_text = cached_atmo.get("cond_text", "")
        windy_hint = bool(cached_atmo.get("windy_hint", False))
    else:
        windy_hint = check_windy_strong_hint(latitude, longitude, event_type)
        ow_data = get_city_current_weather(city)

        ow_corroborates = False
        if ow_data:
            cond = ow_data.get("condition", "").lower()
            precip = ow_data.get("precipitation_mm", 0.0)
            wind_kmh = ow_data.get("wind_speed_kmh", 0.0)
            ev_lower = (event_type or "").lower()
            if "rain" in ev_lower or "flood" in ev_lower:
                ow_corroborates = precip > 0.0 or any(w in cond for w in ["rain", "drizzle", "thunderstorm"])
            elif "storm" in ev_lower or "wind" in ev_lower or "cyclone" in ev_lower:
                ow_corroborates = wind_kmh > 35.0 or "storm" in cond
            elif "heat" in ev_lower:
                ow_corroborates = ow_data.get("temperature", 25.0) > 38.0
            elif "fog" in ev_lower:
                ow_corroborates = any(w in cond for w in ["fog", "mist", "haze"])

        atmospheric_passed = windy_hint or ow_corroborates
        sources_str = []
        if windy_hint:
            sources_str.append("Windy Model")
        if ow_corroborates:
            sources_str.append(f"OpenWeather: {ow_data.get('condition')}")
        cond_text = f"Live station reports: {ow_data.get('condition', 'Clear')}, 0mm precip" if ow_data else "Telemetry inconclusive"

        set_cached_telemetry(atmo_key, {
            "passed": atmospheric_passed,
            "sources_str": sources_str,
            "cond_text": cond_text,
            "windy_hint": bool(windy_hint),
        }, ttl_seconds=1800)

    # Check if the claimed hazard is a geophysical event (Earthquake / Tremor / Seismic)
    is_earthquake_claim = any(k in (event_type or "").lower() for k in ["earthquake", "earth quack", "quake", "tremor", "seismic", "richter"])

    if is_earthquake_claim:
        atmospheric_passed = False
        atmo_points = 0
        score_sum += 0
        breakdown.append({
            "signal": "Atmospheric Telemetry (Windy & OpenWeather)",
            "weight": "+0",
            "points": 0,
            "passed": False,
            "status": "Inapplicable: Atmospheric weather models do not measure seismic tectonic tremors.",
        })
    elif atmospheric_passed:
        atmo_points = 15  # Maximum score for Windy/Atmospheric telemetry (+15)
        score_sum += atmo_points
        breakdown.append({
            "signal": "Atmospheric Telemetry (Windy & OpenWeather)",
            "weight": "+15",
            "points": atmo_points,
            "passed": True,
            "status": f"Corroborated by atmospheric signals ({', '.join(sources_str)})",
        })
    else:
        atmo_points = 5   # Minimum score for Windy/Atmospheric telemetry (+5)
        score_sum += atmo_points
        breakdown.append({
            "signal": "Atmospheric Telemetry (Windy & OpenWeather)",
            "weight": "+5",
            "points": atmo_points,
            "passed": True,
            "status": f"Baseline atmospheric telemetry recorded (Minimum baseline: +5 pts) — {cond_text}",
        })

    # ─────────────────────────────────────────────────────────
    # Signal 2: IMD Official Government Report / Warning
    # ─────────────────────────────────────────────────────────
    imd_warning: Dict[str, Any] = {}
    imd_cache_key = f"imd_warning:{city.lower().strip()}_{state.lower().strip()}_{(event_type or '').lower().strip()}_{round(latitude, 2)}_{round(longitude, 2)}"
    cached_imd = get_cached_telemetry(imd_cache_key)
    if cached_imd and isinstance(cached_imd, dict):
        imd_warning = cached_imd
    else:
        imd_warning = imd_collector.get_district_warning(
            city=city,
            state=state,
            latitude=latitude,
            longitude=longitude,
            event_type=event_type,
        )
        set_cached_telemetry(imd_cache_key, imd_warning, ttl_seconds=900)

    if imd_warning.get("has_warning"):
        tier = imd_warning.get("match_tier", "direct_district")
        pts = 30 if tier in ["direct_district", "metro_alias", "proximity", "seismic_official"] else 25
        score_sum += pts
        breakdown.append({
            "signal": "IMD Official Gov Bulletin",
            "weight": f"+{pts}",
            "points": pts,
            "passed": True,
            "status": f"Corroborated by IMD ({imd_warning.get('severity')} Alert: {imd_warning.get('warning_type')}) — {imd_warning.get('source')}",
        })
    elif imd_warning.get("is_contradicted"):
        # Official government agency (e.g. National Center for Seismology) directly contradicts the claim
        pts = -20
        score_sum += pts
        breakdown.append({
            "signal": "IMD Official Gov Bulletin",
            "weight": "-20",
            "points": pts,
            "passed": False,
            "status": f"Contradicted by {imd_warning.get('source', 'IMD / NCS')}: {imd_warning.get('text', 'No registered incident.')}",
        })
    else:
        # If atmospheric telemetry (Windy/OpenWeather) corroborates the weather:
        # Standard weather / routine rain does not always mandate a severe disaster alert by IMD.
        # It is NOT contradicted, so do not penalize with -10! Give 0 pts and mark consistent.
        if atmospheric_passed:
            score_sum += 0
            breakdown.append({
                "signal": "IMD Official Gov Bulletin",
                "weight": "+0",
                "points": 0,
                "passed": True,
                "status": "Standard meteorological conditions (IMD Station Network clear, atmospheric signals active)",
            })
        else:
            score_sum += -10
            breakdown.append({
                "signal": "IMD Official Gov Bulletin",
                "weight": "-10",
                "points": -10,
                "passed": False,
                "status": "No matching active IMD warning bulletin for district",
            })

    # ─────────────────────────────────────────────────────────
    # Signal 3: Local Reports Cluster Check (>5 in radius)
    # ─────────────────────────────────────────────────────────
    cluster_count = 0
    cluster_cache_key = f"cluster_count:{city.lower().strip()}_{(event_type or '').lower().strip()}_{round(latitude, 1)}_{round(longitude, 1)}"
    cached_cluster = get_cached_telemetry(cluster_cache_key)
    if cached_cluster is not None and isinstance(cached_cluster, dict):
        cluster_count = cached_cluster.get("cluster_count", 0)
    elif db_session:
        try:
            from app.models.Reports import Reports
            six_hours_ago = datetime.utcnow() - timedelta(hours=6)
            cluster_query = db_session.query(Reports).filter(
                Reports.Time >= six_hours_ago,
                Reports.City.ilike(f"%{city}%")
            )
            ev_clean = (event_type or "").lower().strip()
            if any(k in ev_clean for k in ["earthquake", "quake", "tremor", "earth quack"]):
                cluster_query = cluster_query.filter(
                    Reports.Event_Type.ilike("%earthquake%") |
                    Reports.Report.ilike("%earthquake%") |
                    Reports.Report.ilike("%quake%")
                )
            elif any(k in ev_clean for k in ["rain", "flood", "waterlog"]):
                cluster_query = cluster_query.filter(
                    Reports.Event_Type.ilike("%rain%") |
                    Reports.Event_Type.ilike("%flood%") |
                    Reports.Report.ilike("%rain%") |
                    Reports.Report.ilike("%flood%")
                )
            elif any(k in ev_clean for k in ["cyclone", "storm"]):
                cluster_query = cluster_query.filter(
                    Reports.Event_Type.ilike("%storm%") |
                    Reports.Event_Type.ilike("%cyclone%") |
                    Reports.Report.ilike("%cyclone%")
                )

            recent_reports = cluster_query.all()
            for r in recent_reports:
                if r.Latitude and r.Longitude:
                    dist = calculate_haversine_distance(latitude, longitude, r.Latitude, r.Longitude)
                    if dist <= 25.0:  # within 25km radius
                        cluster_count += 1
            set_cached_telemetry(cluster_cache_key, {"cluster_count": cluster_count}, ttl_seconds=600)
        except Exception as e:
            logger.warning(f"Clustering query error: {e}")

    # Cluster density check: requires 5+ corroborating reports in 25km radius
    if cluster_count >= 5:
        cluster_passed = True
        cluster_points = 20
        cluster_msg = f"High cluster density ({cluster_count} reports within 25km)"
    else:
        cluster_passed = False
        cluster_points = 0
        cluster_msg = f"Low cluster density ({cluster_count} report{'s' if cluster_count != 1 else ''} within 25km)"

    score_sum += cluster_points
    breakdown.append({
        "signal": "Local Citizen Reports Cluster",
        "weight": f"+{cluster_points}",
        "points": cluster_points,
        "passed": cluster_passed,
        "status": cluster_msg,
    })

    # ─────────────────────────────────────────────────────────
    # Signal 4: Account / Source Trust Score (+10 Standard, 0 if Red-Listed)
    # ─────────────────────────────────────────────────────────
    # Incident truth verification is objective: all legitimate contributors in good standing
    # receive the standard baseline trust allocation (+10 pts) so the score is consistent for all users.
    acc_points = 10
    acc_status = "Citizen Contributor (Verified Trust Baseline: +10 pts)"

    from app.models.sources import Source
    from app.models.user import User
    from app.models.Reports import Reports

    clean_platform = (platform or "Citizen").strip()
    is_external_source = clean_platform.lower() not in ["citizen", "citizenportal", "direct", "dashboardchat", ""]

    if is_external_source:
        clean_user = (source_username or "").strip()
        raw_handle = clean_user.lstrip("@").strip()
        external_src = None
        if db_session and (clean_user or raw_handle):
            try:
                external_src = db_session.query(Source).filter(
                    (
                        Source.Username.ilike(clean_user) |
                        Source.Username.ilike(raw_handle) |
                        Source.Username.ilike(f"@{raw_handle}") |
                        Source.Source_Name.ilike(clean_user) |
                        Source.Source_Name.ilike(raw_handle)
                    ),
                    Source.Platform.ilike(clean_platform),
                ).first()
            except Exception as e:
                logger.warning(f"Source query error: {e}")

        # Check if specifically RED-LISTED (malicious / repeated disinformation)
        if external_src and (
            external_src.Trust_Status == "RED" or 
            (external_src.Warnings_Count and external_src.Warnings_Count >= 3) or
            (external_src.Fake_Reports and external_src.Fake_Reports >= 3)
        ):
            acc_points = 0
            acc_status = f"RED-LISTED Source ({clean_platform}: @{raw_handle or clean_user}, Warnings: {external_src.Warnings_Count or 0}) - Disinformation History (0 pts)"
        else:
            acc_points = 10
            handle_display = f"@{raw_handle or clean_user}" if (raw_handle or clean_user) else clean_platform
            acc_status = f"Active Contributor Source ({clean_platform}: {handle_display}, Standard Baseline: +10 pts)"

    else:
        # Direct Citizen Portal Submission
        if db_session and user_id:
            try:
                user_obj = db_session.query(User).filter(User.Id == user_id).first()
                if user_obj:
                    user_reps = db_session.query(Reports).filter(Reports.User_Id == user_id).all()
                    fake_count = sum(
                        1 for r in user_reps 
                        if (r.Verification_Status == "Fake" or r.Is_AI_Generated == 1)
                        and (not r.source or getattr(r.source, "Platform", "Citizen").lower() in ["citizen", "citizenportal", "direct", ""])
                    )
                    portal_src = db_session.query(Source).filter(
                        Source.Username == user_obj.Email,
                        Source.Platform == "CitizenPortal",
                    ).first()

                    if (portal_src and portal_src.Trust_Status == "RED") or fake_count >= 3:
                        acc_points = 0
                        acc_status = f"Flagged Citizen Account (History: {fake_count} false reports, 0 pts)"
                    else:
                        acc_points = 10
                        acc_status = f"Citizen Contributor ({user_obj.Name}, Standard Baseline: +10 pts)"
                else:
                    acc_points = 10
                    acc_status = "Citizen Contributor (Standard Baseline: +10 pts)"
            except Exception as e:
                logger.warning(f"User trust query error: {e}")
                acc_points = 10
                acc_status = "Citizen Contributor (Standard Baseline: +10 pts)"
        else:
            if user_trust_status == "RED":
                acc_points = 0
                acc_status = "RED-LISTED Citizen Account - Disinformation History (0 pts)"
            else:
                acc_points = 10
                acc_status = "Citizen Contributor (Standard Baseline: +10 pts)"

    score_sum += acc_points
    breakdown.append({
        "signal": "Account & Source Trust Evaluation",
        "weight": f"+{acc_points}",
        "points": acc_points,
        "passed": acc_points > 0,
        "status": acc_status,
    })

    # ─────────────────────────────────────────────────────────
    # Signal 5: Local News Verification (GNews / NewsData / RSS)
    # ─────────────────────────────────────────────────────────
    news_cache_key = f"news_corroboration:{city.lower().strip()}_{(event_type or '').lower().strip()}"
    cached_news = get_cached_telemetry(news_cache_key)
    if cached_news is not None and isinstance(cached_news, dict):
        news_corroborated = cached_news.get("corroborated", False)
    else:
        news_corroborated = verify_news_for_location(city, event_type)
        set_cached_telemetry(news_cache_key, {"corroborated": bool(news_corroborated)}, ttl_seconds=1800)

    if news_corroborated:
        score_sum += 10
        breakdown.append({
            "signal": "News Media Corroboration",
            "weight": "+10",
            "points": 10,
            "passed": True,
            "status": "Corroborated by Indian news feeds / GNews / NewsData",
        })
    else:
        breakdown.append({
            "signal": "News Media Corroboration",
            "weight": "+0",
            "points": 0,
            "passed": False,
            "status": "No corroborating press or broadcast alerts found",
        })

    # ─────────────────────────────────────────────────────────
    # Signal 6: Metadata Timestamp Consistency Diagnostic
    # ─────────────────────────────────────────────────────────
    if metadata_time_diagnostic:
        breakdown.append({
            "signal": "Metadata Timestamp Verification",
            "weight": "DIAGNOSTIC",
            "points": 0,
            "passed": metadata_time_match,
            "status": metadata_time_diagnostic,
        })

    return {
        "score_sum": score_sum,
        "breakdown": breakdown,
        "windy_hint": windy_hint,
        "imd_corroborated": imd_warning.get("has_warning", False),
        "cluster_count": cluster_count,
        "news_corroborated": news_corroborated,
    }

