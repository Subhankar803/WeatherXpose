import os
import sys
import json
import hashlib
import bcrypt
from datetime import datetime, timedelta

# Ensure parent root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database_setup import SessionLocal, Base, engine
from app.models import User, Admin, Source, Reports, Images_Videos, Action_Log
from app.services.cache_service import add_highlighted_event, set_location_weather
from app.ingestion.openweather_collector import get_city_current_weather


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


def seed_database():
    print("[seed_data] Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Sources
        sources_data = [
            {"Source_Name": "Citizen Reporting Portal", "Platform": "Citizen Report", "Trust_Score": 75.0, "Total_Claims": 120, "True_Claims": 90, "False_Claims": 30},
            {"Source_Name": "IMD Official Bulletins", "Platform": "Gov API", "Trust_Score": 98.0, "Total_Claims": 500, "True_Claims": 490, "False_Claims": 10},
            {"Source_Name": "GNews India Weather Stream", "Platform": "News Media", "Trust_Score": 88.0, "Total_Claims": 210, "True_Claims": 185, "False_Claims": 25},
            {"Source_Name": "NewsData.io Feeds", "Platform": "News Media", "Trust_Score": 85.0, "Total_Claims": 140, "True_Claims": 119, "False_Claims": 21},
            {"Source_Name": "Twitter / X (#IMD #WeatherAlert)", "Platform": "Social Media", "Trust_Score": 62.0, "Total_Claims": 340, "True_Claims": 210, "False_Claims": 130},
            {"Source_Name": "Reddit (r/india / r/mumbai)", "Platform": "Social Media", "Trust_Score": 58.0, "Total_Claims": 95, "True_Claims": 55, "False_Claims": 40},
        ]

        for s_info in sources_data:
            existing = db.query(Source).filter(Source.Source_Name == s_info["Source_Name"]).first()
            if not existing:
                s = Source(
                    Source_Name=s_info["Source_Name"],
                    Platform=s_info["Platform"],
                    Total_Claims=s_info["Total_Claims"],
                    True_Claims=s_info["True_Claims"],
                    False_Claims=s_info["False_Claims"],
                    First_Seen=datetime.utcnow() - timedelta(days=60),
                    Last_Seen=datetime.utcnow(),
                )
                db.add(s)
        db.commit()

        # 2. Seed Admin
        admin = db.query(Admin).filter(Admin.Email == "admin@weather.gov.in").first()
        if not admin:
            admin = Admin(
                Name="Super Administrator",
                Email="admin@weather.gov.in",
                Password=_hash("Admin@12345"),
                Permission_Level="Super Admin",
                Last_Active=datetime.utcnow(),
                Created_at=datetime.utcnow(),
            )
            db.add(admin)

        reviewer = db.query(Admin).filter(Admin.Email == "reviewer@weather.gov.in").first()
        if not reviewer:
            reviewer = Admin(
                Name="Duty Forecaster / Reviewer",
                Email="reviewer@weather.gov.in",
                Password=_hash("Reviewer@12345"),
                Permission_Level="Reviewer",
                Last_Active=datetime.utcnow(),
                Created_at=datetime.utcnow(),
            )
            db.add(reviewer)
        db.commit()

        # 3. Seed Users and CitizenPortal Sources
        users_data = [
            {
                "Name": "Rajesh Kumar (Verified Spotter)",
                "Email": "rajesh.spotter@gmail.com",
                "Password": _hash("Password@123"),
                "Location": "Mumbai, Maharashtra",
                "Trust_Status": "GREEN",
                "Total_Reports": 18,
                "Fake_Reports": 0,
                "Warnings_Count": 0,
            },
            {
                "Name": "Pooja Sharma (Community Reporter)",
                "Email": "pooja.reporter@gmail.com",
                "Password": _hash("Password@123"),
                "Location": "Kolkata, West Bengal",
                "Trust_Status": "GREEN",
                "Total_Reports": 12,
                "Fake_Reports": 0,
                "Warnings_Count": 0,
            },
            {
                "Name": "Amit Roy (New Contributor)",
                "Email": "amit.roy2026@gmail.com",
                "Password": _hash("Password@123"),
                "Location": "Guwahati, Assam",
                "Trust_Status": "GREY",
                "Total_Reports": 1,
                "Fake_Reports": 0,
                "Warnings_Count": 1,
            },
            {
                "Name": "Spam Bot 404 (Disinformation Node)",
                "Email": "bot404@fakenews.net",
                "Password": _hash("Password@123"),
                "Location": "Delhi",
                "Trust_Status": "RED",
                "Total_Reports": 6,
                "Fake_Reports": 6,
                "Warnings_Count": 3,
                "Is_Active": False,
            }
        ]

        for u_data in users_data:
            existing_u = db.query(User).filter(User.Email == u_data["Email"]).first()
            if not existing_u:
                u = User(
                    Name=u_data["Name"],
                    Email=u_data["Email"],
                    Password=u_data["Password"],
                    Location=u_data["Location"],
                    Is_Active=u_data.get("Is_Active", True),
                )
                db.add(u)
                db.flush()

            existing_src = db.query(Source).filter(
                Source.Username == u_data["Email"],
                Source.Platform == "CitizenPortal",
            ).first()
            if not existing_src:
                src = Source(
                    Username=u_data["Email"],
                    Source_Name=u_data["Name"],
                    Platform="CitizenPortal",
                    Trust_Status=u_data["Trust_Status"],
                    Total_Reports=u_data["Total_Reports"],
                    Fake_Reports=u_data["Fake_Reports"],
                    Warnings_Count=u_data["Warnings_Count"],
                    Total_Claims=u_data["Total_Reports"],
                    True_Claims=u_data["Total_Reports"] - u_data["Fake_Reports"],
                    False_Claims=u_data["Fake_Reports"],
                    Trust_Score=round(((u_data["Total_Reports"] - u_data["Fake_Reports"]) / max(1, u_data["Total_Reports"])) * 100.0, 1),
                )
                db.add(src)
        db.commit()

        # 4. Seed Realistic Indian Weather Reports
        if db.query(Reports).count() == 0:
            now = datetime.utcnow()

            # Dynamically look up IDs to guarantee foreign keys match
            user1 = db.query(User).filter(User.Email == "rajesh.spotter@gmail.com").first()
            user2 = db.query(User).filter(User.Email == "pooja.reporter@gmail.com").first()
            user3 = db.query(User).filter(User.Email == "amit.roy2026@gmail.com").first()
            user4 = db.query(User).filter(User.Email == "bot404@fakenews.net").first()

            src_citizen = db.query(Source).filter(Source.Source_Name == "Citizen Reporting Portal").first()
            src_gnews = db.query(Source).filter(Source.Source_Name == "GNews India Weather Stream").first()
            src_social = db.query(Source).filter(Source.Source_Name == "Twitter / X (#IMD #WeatherAlert)").first()

            u1_id = user1.Id if user1 else 1
            u2_id = user2.Id if user2 else 2
            u3_id = user3.Id if user3 else 3
            u4_id = user4.Id if user4 else 4

            c_src_id = src_citizen.Id if src_citizen else (db.query(Source.Id).first() or [1])[0]
            g_src_id = src_gnews.Id if src_gnews else c_src_id
            s_src_id = src_social.Id if src_social else c_src_id

            reports_seed = [
                {
                    "User_Id": u1_id,
                    "Source_Id": c_src_id,
                    "Report": "Severe waterlogging near Dadar TT circle and Hindmata, water depth approx 3.5 feet following 180mm continuous rainfall. Traffic diverted.",
                    "Time": now - timedelta(hours=2),
                    "City": "Mumbai",
                    "State": "Maharashtra",
                    "Latitude": 19.0178,
                    "Longitude": 72.8478,
                    "Event_Type": "flooding",
                    "Img_Vid_Url": "https://images.unsplash.com/photo-1547683905-f686c993aae5?w=800&q=80",
                    "Verification_Score": 85.0,
                    "Verification_Status": "Othentic",
                    "Hint_Breakdown": json.dumps([
                        {"signal": "Windy Atmospheric Telemetry", "points": 15, "passed": True, "status": "Strong rainfall detected (48mm/h)"},
                        {"signal": "IMD Official Gov Bulletin", "points": 30, "passed": True, "status": "IMD Red Alert Active for Mumbai"},
                        {"signal": "Local Citizen Reports Cluster", "points": 20, "passed": True, "status": "14 reports clustered in Dadar area"},
                        {"signal": "Account Trust Evaluation", "points": 10, "passed": True, "status": "Verified Account (Green)"},
                        {"signal": "News Media Corroboration", "points": 10, "passed": True, "status": "Top stories on NDTV & Times of India"},
                    ]),
                    "Is_AI_Generated": 0,
                },
                {
                    "User_Id": u2_id,
                    "Source_Id": c_src_id,
                    "Report": "Intense lightning strikes and thunderstorm activity over Salt Lake Sector V and EM Bypass. Tree branches fallen on road.",
                    "Time": now - timedelta(hours=4),
                    "City": "Kolkata",
                    "State": "West Bengal",
                    "Latitude": 22.5868,
                    "Longitude": 88.4178,
                    "Event_Type": "thunderstorm",
                    "Img_Vid_Url": "https://images.unsplash.com/photo-1605727216801-e27ce1d0cc28?w=800&q=80",
                    "Verification_Score": 77.0,
                    "Verification_Status": "Othentic",
                    "Hint_Breakdown": json.dumps([
                        {"signal": "Windy Atmospheric Telemetry", "points": 15, "passed": True, "status": "High convective wind gusts (52 km/h)"},
                        {"signal": "IMD Official Gov Bulletin", "points": 30, "passed": True, "status": "IMD Orange Thunderstorm Nowcast"},
                        {"signal": "Local Citizen Reports Cluster", "points": 20, "passed": True, "status": "8 reports in Salt Lake"},
                        {"signal": "Account Trust Evaluation", "points": 10, "passed": True, "status": "Verified Account (Green)"},
                        {"signal": "News Media Corroboration", "points": 2, "passed": True, "status": "Regional news bulletin"},
                    ]),
                    "Is_AI_Generated": 0,
                },
                {
                    "User_Id": u3_id,
                    "Source_Id": c_src_id,
                    "Report": "Submerged paddy fields and rising water level in Brahmaputra river near Fancy Bazar, Guwahati.",
                    "Time": now - timedelta(hours=1),
                    "City": "Guwahati",
                    "State": "Assam",
                    "Latitude": 26.1850,
                    "Longitude": 91.7450,
                    "Event_Type": "flooding",
                    "Img_Vid_Url": "https://images.unsplash.com/photo-1514632595-4944383f2737?w=800&q=80",
                    "Verification_Score": 55.0,
                    "Verification_Status": "Underprocess",
                    "Hint_Breakdown": json.dumps([
                        {"signal": "Windy Atmospheric Telemetry", "points": 15, "passed": True, "status": "Moderate rain (12mm)"},
                        {"signal": "IMD Official Gov Bulletin", "points": -10, "passed": False, "status": "No specific district flood warning yet"},
                        {"signal": "Local Citizen Reports Cluster", "points": 20, "passed": True, "status": "6 reports in Kamrup Metro"},
                        {"signal": "Account Trust Evaluation", "points": 2, "passed": True, "status": "New account (Grey list)"},
                        {"signal": "News Media Corroboration", "points": 10, "passed": True, "status": "Local Assam news live broadcast"},
                    ]),
                    "Is_AI_Generated": 0,
                },
                {
                    "User_Id": u4_id,
                    "Source_Id": s_src_id,
                    "Report": "Tsunami waves spotted hitting India Gate Delhi after mysterious earthquake! Total destruction downtown!",
                    "Time": now - timedelta(minutes=30),
                    "City": "Delhi",
                    "State": "Delhi",
                    "Latitude": 28.6129,
                    "Longitude": 77.2295,
                    "Event_Type": "flooding",
                    "Img_Vid_Url": "https://images.unsplash.com/photo-1547683905-f686c993aae5?w=800&q=80",
                    "Verification_Score": 0.0,
                    "Verification_Status": "Fake",
                    "Hint_Breakdown": json.dumps([
                        {"signal": "Image / Media Forensics", "points": 0, "passed": False, "status": "AI Synthetic Deepfake image detected (Confidence: 96%) - Midjourney signature"},
                        {"signal": "IMD Official Gov Bulletin", "points": -10, "passed": False, "status": "IMD reports dry clear sky (42°C)"},
                        {"signal": "Account Trust Evaluation", "points": 0, "passed": False, "status": "Account flagged as RED / Disinformation Bot"},
                    ]),
                    "Is_AI_Generated": 1,
                },
                {
                    "User_Id": u1_id,
                    "Source_Id": g_src_id,
                    "Report": "Severe Heatwave alert issued for Jaipur and western Rajasthan with daytime temperatures touching 46.2°C.",
                    "Time": now - timedelta(days=1),
                    "City": "Jaipur",
                    "State": "Rajasthan",
                    "Latitude": 26.9124,
                    "Longitude": 75.7873,
                    "Event_Type": "heatwave",
                    "Img_Vid_Url": "https://images.unsplash.com/photo-1504370805625-d32c54b16100?w=800&q=80",
                    "Verification_Score": 90.0,
                    "Verification_Status": "Othentic",
                    "Hint_Breakdown": json.dumps([
                        {"signal": "Windy Atmospheric Telemetry", "points": 15, "passed": True, "status": "Extreme surface temperature (45.8°C)"},
                        {"signal": "IMD Official Gov Bulletin", "points": 30, "passed": True, "status": "IMD Red Heatwave Warning"},
                        {"signal": "Local Citizen Reports Cluster", "points": 20, "passed": True, "status": "Multiple reports from Jaipur district"},
                        {"signal": "Account Trust Evaluation", "points": 10, "passed": True, "status": "Verified Account"},
                        {"signal": "News Media Corroboration", "points": 10, "passed": True, "status": "Rajasthan Patrika & PIB Alerts"},
                    ]),
                    "Is_AI_Generated": 0,
                }
            ]

            for r_data in reports_seed:
                rep = Reports(**r_data)
                db.add(rep)
                db.flush()
                if rep.Verification_Status == "Othentic":
                    add_highlighted_event(rep.City, {
                        "city": rep.City,
                        "state": rep.State,
                        "latitude": rep.Latitude,
                        "longitude": rep.Longitude,
                        "event_type": rep.Event_Type,
                        "description": rep.Report,
                        "verification_score": rep.Verification_Score,
                        "status": rep.Verification_Status,
                        "timestamp": rep.Time.isoformat(),
                    })
            db.commit()

        print("[seed_data] Database seeded successfully with Indian weather events and demo users.")

    except Exception as e:
        print(f"[seed_data] Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
