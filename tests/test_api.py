"""
FastAPI REST API Integration Tests using TestClient.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Verify health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["docs_url"] == "/docs"


def test_public_reports_filter():
    """Verify date/event/location report queries."""
    response = client.get("/api/reports?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "total_records" in data
    assert "data" in data


def test_map_active_incidents():
    """Verify geospatial GeoJSON format."""
    response = client.get("/api/map/active-incidents")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data


def test_dashboard_stats():
    """Verify Big Data aggregated KPI statistics."""
    response = client.get("/api/stats/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "total_claims_processed" in data
    assert "verified_authentic_claims" in data
    assert "platform_authenticity_rate" in data


def test_live_weather_grid():
    """Verify Tier 1 Cache weather telemetry."""
    response = client.get("/api/weather/live-grid")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert len(data["data"]) > 0
    # Check natural weather columns
    first_station = data["data"][0]
    assert "temperature" in first_station
    assert "rainfall" in first_station


def test_active_7day_events():
    """Verify Tier 2 Cache 7-day severe events feed."""
    response = client.get("/api/events/7day-active")
    assert response.status_code == 200
    data = response.json()
    assert "active_events_count" in data


def test_ml_city_evaluate():
    """Verify ML multi-model data fusion for Indian cities."""
    response = client.get("/api/evaluate/Mumbai")
    assert response.status_code == 200
    data = response.json()
    assert data["city"] == "Mumbai"
    assert "ml_inference" in data
    assert "flood_probability_score" in data["ml_inference"]


def test_citizen_report_submission():
    """Verify citizen report submission with form structure, platform, username, and instant truth scoring."""
    payload = {
        "city": "Kolkata",
        "state": "West Bengal",
        "event_type": "thunderstorm",
        "report_text": "Severe thunderstorm with lightning strikes over Salt Lake.",
        "incident_time": "2026-09-08 14:00",
        "platform": "Instagram",
        "source_username": "kolkata_weather_watcher",
        "latitude": 22.5726,
        "longitude": 88.3639,
    }
    response = client.post("/api/citizen-report/", data=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "verification_status" in data["data"]
    assert "verification_score" in data["data"]
    assert "hint_breakdown" in data["data"]


def test_chat_query_mode():
    """Verify normal dashboard chat query mode (when user hasn't attached an image/video)."""
    response = client.get("/api/citizen-report/chat-query?city=Mumbai&query=Is+there+heavy+rainfall+in+Mumbai")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["mode"] == "chat_query"
    assert "result" in data


def test_admin_endpoints():
    """Verify admin endpoints and review queue using valid Admin token."""
    # Register / login admin to get admin token
    admin_email = "test.api.admin@weather.gov.in"
    otp_res = client.post("/api/auth/otp/send-email", json={"email": admin_email}).json()
    reg_res = client.post("/api/auth/admin/register", json={
        "name": "API Admin",
        "email": admin_email,
        "password": "AdminPassword@123",
        "admin_auth_code": "SIH2026@DEBUGDYNASTY",
        "email_otp": otp_res["email_otp"],
        "permission_level": "Super Admin",
    })
    if reg_res.status_code == 201:
        admin_token = reg_res.json()["access_token"]
    else:
        login_res = client.post("/api/auth/admin/login", json={
            "email": admin_email,
            "password": "AdminPassword@123",
        })
        admin_token = login_res.json()["access_token"]

    headers = {"Authorization": f"Bearer {admin_token}"}

    # Test pending queue
    response = client.get("/api/admin/pending-review", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "pending_count" in data

    # Test telemetry
    resp_tel = client.get("/api/admin/system-telemetry", headers=headers)
    assert resp_tel.status_code == 200
    assert resp_tel.json()["status"] == "operational"


if __name__ == "__main__":
    print("Running API integration tests...")
    test_health_check()
    print("[PASS] test_health_check")
    test_public_reports_filter()
    print("[PASS] test_public_reports_filter")
    test_map_active_incidents()
    print("[PASS] test_map_active_incidents")
    test_dashboard_stats()
    print("[PASS] test_dashboard_stats")
    test_live_weather_grid()
    print("[PASS] test_live_weather_grid")
    test_active_7day_events()
    print("[PASS] test_active_7day_events")
    test_ml_city_evaluate()
    print("[PASS] test_ml_city_evaluate")
    test_citizen_report_submission()
    print("[PASS] test_citizen_report_submission")
    test_chat_query_mode()
    print("[PASS] test_chat_query_mode")
    test_admin_endpoints()
    print("[PASS] test_admin_endpoints")
    print("\nALL API INTEGRATION TESTS PASSED SUCCESSFULLY!")
