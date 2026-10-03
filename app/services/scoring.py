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
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.ingestion.windy_collector import check_windy_strong_hint, evaluate_windy_telemetry
from app.ingestion.openweather_collector import get_city_current_weather
from app.ingestion.imd_collector import IMDCollector, is_hazard_compatible
from app.ingestion.newsdata_collector import verify_news_for_location
from app.ml.duplicate_detector import calculate_haversine_distance
from app.services.cache_service import get_cached_telemetry, set_cached_telemetry, get_city_active_7day_events
from app.services.image_forensics import parse_datetime_flexible

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
    incident_time: Optional[Union[str, datetime]] = None,
) -> Dict[str, Any]:
    """
    Evaluates all truth signals and calculates the cumulative hint score `sum`.
    Utilizes disk-persistent telemetry caching to prevent API jitter and score fluctuations.
    Supports incident_time targeting for exact historical and ongoing date corroboration.
    """
    score_sum = 0
    breakdown: List[Dict[str, Any]] = []
    windy_hint: bool = False

    # ─────────────────────────────────────────────────────────
    # Parse exact incident date/time if provided
    # ─────────────────────────────────────────────────────────
    parsed_dt = None
    date_str = ""
    if incident_time:
        if isinstance(incident_time, datetime):
            parsed_dt = incident_time
        else:
            parsed_dt = parse_datetime_flexible(str(incident_time))
        if parsed_dt:
            date_str = parsed_dt.strftime("%Y-%m-%d")
        else:
            date_str = str(incident_time)[:10]

    # ─────────────────────────────────────────────────────────
    # Signal 1: Atmospheric Telemetry (Windy Model + OpenWeather Live Station)
    # ─────────────────────────────────────────────────────────
    atmo_key = f"atmospheric_telemetry:{city.lower().strip()}_{(event_type or '').lower().strip()}_{round(latitude, 2)}_{round(longitude, 2)}"
    if date_str:
        atmo_key += f"_{date_str}"

    cached_atmo = get_cached_telemetry(atmo_key)
    if cached_atmo and isinstance(cached_atmo, dict) and "points" in cached_atmo:
        atmo_points = int(cached_atmo.get("points", 5))
        atmo_status = str(cached_atmo.get("status", ""))
        atmospheric_passed = bool(cached_atmo.get("passed", False))
        windy_hint = bool(cached_atmo.get("windy_hint", False))
    else:
        windy_eval = evaluate_windy_telemetry(latitude, longitude, event_type, incident_time=incident_time)
        windy_hint = bool(windy_eval.get("passed", False))
        is_outside_window = bool(windy_eval.get("is_historical_outside_window", False))

        ow_data = get_city_current_weather(city)
        ow_corroborates = False
        ow_severity_pts = 0
        if ow_data:
            cond = (ow_data.get("condition") or "").lower()
            precip = float(ow_data.get("precipitation_mm", 0.0) or 0.0)
            wind_kmh = float(ow_data.get("wind_speed_kmh", 0.0) or 0.0)
            ev_lower = (event_type or "").lower()
            if any(k in ev_lower for k in ["rain", "flood", "waterlog", "shower", "cloudburst", "drizzle"]):
                if precip >= 15.0 or "torrential" in cond:
                    ow_corroborates = True
                    ow_severity_pts = 15
                elif precip >= 5.0 or any(w in cond for w in ["heavy", "thunderstorm", "shower"]):
                    ow_corroborates = True
                    ow_severity_pts = 12
                elif precip > 0.0 or any(w in cond for w in ["rain", "drizzle"]):
                    ow_corroborates = True
                    ow_severity_pts = 9
            elif any(k in ev_lower for k in ["storm", "wind", "cyclone", "thunder", "gale", "squall"]):
                if wind_kmh >= 50.0:
                    ow_corroborates = True
                    ow_severity_pts = 15
                elif wind_kmh >= 30.0 or any(w in cond for w in ["storm", "thunder", "squall"]):
                    ow_corroborates = True
                    ow_severity_pts = 12
                elif wind_kmh >= 18.0:
                    ow_corroborates = True
                    ow_severity_pts = 8
            elif "heat" in ev_lower:
                temp = float(ow_data.get("temperature", 25.0) or 25.0)
                if temp >= 42.0:
                    ow_corroborates = True
                    ow_severity_pts = 15
                elif temp >= 39.0:
                    ow_corroborates = True
                    ow_severity_pts = 12
                elif temp >= 36.0:
                    ow_corroborates = True
                    ow_severity_pts = 8
            elif any(k in ev_lower for k in ["fog", "cold", "mist"]):
                temp = float(ow_data.get("temperature", 25.0) or 25.0)
                if any(w in cond for w in ["fog", "mist", "haze"]):
                    ow_corroborates = True
                    ow_severity_pts = 12 if temp <= 12.0 else 8

        # Check historical / date corroboration if user entered exact date
        hist_corroborates = False
        hist_points = 5
        hist_sources: List[str] = []
        if parsed_dt or date_str:
            # 1. Check verified reports in database for that city within ±48h of incident_time
            if db_session and parsed_dt:
                try:
                    from app.models.Reports import Reports
                    two_days_before = parsed_dt - timedelta(days=2)
                    two_days_after = parsed_dt + timedelta(days=2)
                    verified_reps = db_session.query(Reports).filter(
                        Reports.City.ilike(f"%{city}%"),
                        (Reports.Verification_Status == "Othentic") | (Reports.Verification_Score >= 60),
                        Reports.Incident_Time >= two_days_before,
                        Reports.Incident_Time <= two_days_after,
                    ).all()
                    if verified_reps:
                        compat_reps = [r for r in verified_reps if is_hazard_compatible((event_type or "").lower(), (r.Event_Type or "").lower())]
                        if compat_reps:
                            hist_corroborates = True
                            hist_points = 14 if len(compat_reps) >= 5 else 12
                            hist_sources.append(f"{len(compat_reps)} verified reports on {date_str}")
                except Exception as e:
                    logger.warning(f"Error querying verified DB reports for atmospheric check: {e}")

            # 2. Check 7-day highlighted event cache for confirmed events in that city on that date
            if not hist_corroborates:
                try:
                    city_events = get_city_active_7day_events(city)
                    for ev in city_events:
                        ev_t = (ev.get("event_type") or "").lower()
                        req_t = (event_type or "").lower()
                        if is_hazard_compatible(req_t, ev_t):
                            ev_ts = str(ev.get("timestamp", ""))
                            if not date_str or date_str in ev_ts:
                                if ev.get("status") == "Othentic" or ev.get("verification_score", 0) >= 60:
                                    hist_corroborates = True
                                    hist_points = 12
                                    hist_sources.append(f"Confirmed Archive ({ev.get('event_type')})")
                                    break
                except Exception as e:
                    logger.warning(f"Error checking 7-day event cache for atmospheric check: {e}")

        # Compute dynamic situation-based atmospheric points (between 5 and 15)
        if is_outside_window:
            # Historical date outside Windy's 10-day active forecast window
            if hist_corroborates:
                atmo_points = hist_points
                atmo_status = f"Windy Model & Archive: Historical date {date_str} corroborated by {', '.join(hist_sources)} (+{atmo_points} pts)"
                atmospheric_passed = True
            else:
                atmo_points = 5
                atmo_status = f"Windy Model & Archive: Date {date_str or 'specified'} outside 10-day active forecast window; no severe telemetry anomaly confirmed (Minimum baseline: +5 pts)"
                atmospheric_passed = False
        else:
            # Active window: Windy model telemetry provides the authentic numerical baseline/signal
            windy_pts = windy_eval.get("points", 5)
            atmo_points = windy_pts
            atmo_status = windy_eval.get("windy_hint") or windy_eval.get("status", "")

            # If live OpenWeather station also corroborates, elevate score if higher
            if ow_corroborates:
                if ow_severity_pts > atmo_points:
                    atmo_points = min(15, max(atmo_points, ow_severity_pts))
                elif atmo_points < 14:
                    atmo_points = min(15, atmo_points + 2)
                atmo_status += f" | Live Station: {ow_data.get('condition')} ({ow_data.get('precipitation_mm')}mm rain, {ow_data.get('wind_speed_kmh')} km/h wind)"

            atmospheric_passed = atmo_points > 5

        atmo_points = max(5, min(15, atmo_points))

        set_cached_telemetry(atmo_key, {
            "points": atmo_points,
            "status": atmo_status,
            "passed": atmospheric_passed,
            "windy_hint": bool(windy_hint),
        }, ttl_seconds=1800)

    # Check if the claimed hazard is a geophysical event (Earthquake / Tremor / Seismic)
    is_earthquake_claim = any(k in (event_type or "").lower() for k in ["earthquake", "earth quack", "quake", "tremor", "seismic", "richter"])

    if is_earthquake_claim:
        atmo_points = 0
        score_sum += 0
        breakdown.append({
            "signal": "Atmospheric Telemetry (Windy & OpenWeather)",
            "weight": "+0",
            "points": 0,
            "passed": False,
            "status": "Inapplicable: Atmospheric weather models do not measure seismic tectonic tremors.",
        })
    else:
        score_sum += atmo_points
        breakdown.append({
            "signal": "Atmospheric Telemetry (Windy & OpenWeather)",
            "weight": f"+{atmo_points}",
            "points": atmo_points,
            "passed": atmo_points > 5,
            "status": atmo_status,
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
    if db_session:
        try:
            from app.models.Reports import Reports
            if parsed_dt:
                # Query reports within ±48 hours of user-specified incident time
                start_window = parsed_dt - timedelta(hours=48)
                end_window = parsed_dt + timedelta(hours=48)
                cluster_query = db_session.query(Reports).filter(
                    Reports.City.ilike(f"%{city}%"),
                    (
                        (Reports.Incident_Time >= start_window) & (Reports.Incident_Time <= end_window)
                    ) | (
                        (Reports.Time >= start_window) & (Reports.Time <= end_window)
                    )
                )
            else:
                # Live submission without exact historical date: query within last 24 hours
                twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
                cluster_query = db_session.query(Reports).filter(
                    Reports.City.ilike(f"%{city}%"),
                    (Reports.Time >= twenty_four_hours_ago) | (Reports.Incident_Time >= twenty_four_hours_ago)
                )

            ev_clean = (event_type or "").lower().strip()
            if any(k in ev_clean for k in ["earthquake", "quake", "tremor", "earth quack", "seismic"]):
                cluster_query = cluster_query.filter(
                    Reports.Event_Type.ilike("%earthquake%") |
                    Reports.Event_Type.ilike("%quake%") |
                    Reports.Event_Type.ilike("%tremor%") |
                    Reports.Report.ilike("%earthquake%") |
                    Reports.Report.ilike("%quake%")
                )
            elif any(k in ev_clean for k in ["rain", "flood", "waterlog", "storm", "thunder", "cyclone"]):
                cluster_query = cluster_query.filter(
                    Reports.Event_Type.ilike("%rain%") |
                    Reports.Event_Type.ilike("%flood%") |
                    Reports.Event_Type.ilike("%waterlog%") |
                    Reports.Event_Type.ilike("%storm%") |
                    Reports.Event_Type.ilike("%thunder%") |
                    Reports.Event_Type.ilike("%cyclone%") |
                    Reports.Report.ilike("%rain%") |
                    Reports.Report.ilike("%flood%") |
                    Reports.Report.ilike("%waterlog%") |
                    Reports.Report.ilike("%storm%") |
                    Reports.Report.ilike("%thunder%")
                )
            elif any(k in ev_clean for k in ["heat", "heatwave"]):
                cluster_query = cluster_query.filter(
                    Reports.Event_Type.ilike("%heat%") |
                    Reports.Report.ilike("%heat%")
                )
            elif any(k in ev_clean for k in ["fog", "mist", "cold", "visibility"]):
                cluster_query = cluster_query.filter(
                    Reports.Event_Type.ilike("%fog%") |
                    Reports.Event_Type.ilike("%cold%") |
                    Reports.Report.ilike("%fog%")
                )
            elif any(k in ev_clean for k in ["snow", "blizzard", "avalanche"]):
                cluster_query = cluster_query.filter(
                    Reports.Event_Type.ilike("%snow%") |
                    Reports.Report.ilike("%snow%")
                )

            recent_reports = cluster_query.all()
            for r in recent_reports:
                if r.Latitude and r.Longitude:
                    dist = calculate_haversine_distance(latitude, longitude, r.Latitude, r.Longitude)
                    if dist <= 35.0:  # within 35km radius (metropolitan cluster)
                        cluster_count += 1
                elif r.City and city.lower() in r.City.lower():
                    cluster_count += 1
        except Exception as e:
            logger.warning(f"Clustering query error: {e}")

    # Cluster density check: requires 5+ corroborating reports in 25-35km radius (+20 pts)
    # Emerging clusters of 3-4 reports also get (+15 pts) corroboration
    if cluster_count >= 5:
        cluster_passed = True
        cluster_points = 20
        cluster_msg = f"High cluster density ({cluster_count} reports within 25km)"
    elif cluster_count >= 3:
        cluster_passed = True
        cluster_points = 15
        cluster_msg = f"Emerging cluster density ({cluster_count} reports within 25km)"
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
        elif (
            external_src and (
                external_src.Trust_Status == "GREEN" or 
                (external_src.Trust_Score and external_src.Trust_Score >= 70.0 and (external_src.Total_Claims or 0) >= 2)
            )
        ):
            acc_points = 10
            handle_display = f"@{raw_handle or clean_user}" if (raw_handle or clean_user) else clean_platform
            acc_status = f"Verified Social Source ({clean_platform}: {handle_display}, Trust Score: {external_src.Trust_Score}%)"
        elif not external_src or is_first_post or (external_src.Total_Reports or 0) == 0:
            acc_points = 2
            handle_display = f"@{raw_handle or clean_user}" if (raw_handle or clean_user) else clean_platform
            acc_status = f"New Social Source ({clean_platform}: {handle_display}, First Post: +2 pts)"
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
                    elif is_first_post or len(user_reps) == 0:
                        acc_points = 2
                        acc_status = f"New Citizen Account ({user_obj.Name}, First Post: +2 pts)"
                    else:
                        acc_points = 10
                        acc_status = f"Citizen Contributor ({user_obj.Name}, Standard Baseline: +10 pts)"
                else:
                    if is_first_post:
                        acc_points = 2
                        acc_status = "New Citizen Account (First Post: +2 pts)"
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
            elif is_first_post:
                acc_points = 2
                acc_status = "New Citizen Account (First Post: +2 pts)"
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

