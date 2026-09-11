import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.database_setup import Base, engine, SessionLocal
from app.models.user import User
from app.models.admin import Admin

import pytest

client = TestClient(app)


def cleanup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Clean up test accounts
    db.query(User).filter(User.Email.like("test.%@example.com")).delete(synchronize_session=False)
    db.query(Admin).filter(Admin.Email.like("test.%@weather.gov.in")).delete(synchronize_session=False)
    db.commit()
    db.close()


@pytest.fixture(autouse=True)
def clean_database():
    cleanup_db()
    yield
    cleanup_db()


def test_otp_dispatch_and_verification():
    # 1. Send Email OTP
    res = client.post("/api/auth/otp/send-email", json={"email": "test.citizen@example.com"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    email_otp = data["email_otp"]
    assert len(email_otp) == 6

    # 2. Verify Email OTP
    res = client.post("/api/auth/otp/verify", json={
        "channel": "email",
        "identifier": "test.citizen@example.com",
        "otp": email_otp,
    })
    assert res.status_code == 200
    assert res.json()["valid"] is True


def test_resend_otp_and_cooldown_rate_limit():
    from app.services.otp_service import _EMAIL_OTP_STORE
    email = "test.resend.citizen@example.com"

    # Step 1: Initial send
    res = client.post("/api/auth/otp/send-email", json={"email": email})
    assert res.status_code == 200
    first_otp = res.json()["email_otp"]
    assert len(first_otp) == 6

    # Step 2: Immediate resend attempt should fail with 429 Too Many Requests
    resend_fail = client.post("/api/auth/otp/resend", json={"email": email})
    assert resend_fail.status_code == 429
    assert "Retry-After" in resend_fail.headers
    assert "Please wait" in resend_fail.json()["detail"]

    # Step 3: Simulate cooldown expiration by setting last_sent_at back by 35 seconds
    cached_record = _EMAIL_OTP_STORE[email]
    # record: (otp, expires_at, last_sent_at)
    _EMAIL_OTP_STORE[email] = (cached_record[0], cached_record[1], cached_record[2] - 35)

    # Step 4: Resend should now succeed
    resend_ok = client.post("/api/auth/otp/resend", json={"email": email})
    assert resend_ok.status_code == 200
    resend_data = resend_ok.json()
    assert resend_data["status"] == "success"
    second_otp = resend_data["email_otp"]
    assert len(second_otp) == 6

    # Step 5: The old OTP should now fail verification
    old_verify = client.post("/api/auth/otp/verify", json={
        "channel": "email",
        "identifier": email,
        "otp": first_otp,
    })
    # If first_otp happened to be equal to second_otp (1 in a million), skip mismatch assertion
    if first_otp != second_otp:
        assert old_verify.status_code == 400

    # Step 6: The new resent OTP should successfully verify
    new_verify = client.post("/api/auth/otp/verify", json={
        "channel": "email",
        "identifier": email,
        "otp": second_otp,
    })
    assert new_verify.status_code == 200
    assert new_verify.json()["valid"] is True

    # Step 7: Test alias route /api/auth/otp/resend-email
    _EMAIL_OTP_STORE[email] = (second_otp, _EMAIL_OTP_STORE[email][1], _EMAIL_OTP_STORE[email][2] - 35)
    alias_res = client.post("/api/auth/otp/resend-email", json={"email": email})
    assert alias_res.status_code == 200
    assert alias_res.json()["status"] == "success"


def test_gps_location_resolution():
    # Mumbai coordinates
    res = client.post("/api/auth/resolve-location", json={
        "latitude": 19.0760,
        "longitude": 72.8777,
    })
    assert res.status_code == 200
    data = res.json()
    assert data["city"] == "Mumbai"
    assert data["state"] == "Maharashtra"
    assert "Mumbai, Maharashtra" in data["formatted_location"]
    assert data["accuracy"] == "pinpoint"
    assert "suburb" in data and data["suburb"] is not None
    assert "full_address" in data and data["full_address"] is not None
    assert data["postcode"] in data["formatted_location"]

    # 2. Rural / Taluka coordinates (Ghoghamba Taluka, Panchmahal, Gujarat)
    res_taluka = client.post("/api/auth/resolve-location", json={
        "latitude": 22.5615365,
        "longitude": 73.5779587,
    })
    assert res_taluka.status_code == 200
    taluka_data = res_taluka.json()
    assert taluka_data["city"] != "India"
    assert "Ghoghamba" in taluka_data["city"] or "Panchmahal" in taluka_data["city"]
    assert taluka_data["state"] == "Gujarat"
    assert taluka_data["district"] == "Panchmahal"
    assert "India" not in taluka_data["formatted_location"].split(",")[0]
    assert taluka_data["accuracy"] == "pinpoint"


def test_user_registration_with_gps_location_and_otps():
    email = "test.user.gps@example.com"

    # Step 1: Request Email OTP
    otp_res = client.post("/api/auth/otp/send-email", json={"email": email})
    assert otp_res.status_code == 200
    otp_data = otp_res.json()
    email_otp = otp_data["email_otp"]

    # Step 2: Attempt registration with invalid OTP (should fail)
    bad_res = client.post("/api/auth/user/register", json={
        "name": "Test GPS Citizen",
        "email": email,
        "password": "Password@123",
        "email_otp": "000000",
        "latitude": 19.0760,
        "longitude": 72.8777,
    })
    assert bad_res.status_code == 400
    assert "Invalid or expired Email OTP" in bad_res.json()["detail"]

    # Step 3: Register with valid OTP and GPS coordinates
    reg_res = client.post("/api/auth/user/register", json={
        "name": "Test GPS Citizen",
        "email": email,
        "password": "Password@123",
        "email_otp": email_otp,
        "latitude": 19.0760,
        "longitude": 72.8777,
    })
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["role"] == "user"
    assert "access_token" in reg_data
    assert "Mumbai" in reg_data["account_info"]["location"]
    user_token = reg_data["access_token"]

    # Step 4: Login with registered credentials
    login_res = client.post("/api/auth/user/login", json={
        "email": email,
        "password": "Password@123",
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["role"] == "user"

    # Step 5: Test /user/me with user token
    me_res = client.get("/api/auth/user/me", headers={"Authorization": f"Bearer {user_token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email


def test_admin_registration_with_auth_code_and_otps():
    admin_email = "test.admin.ops@weather.gov.in"

    # Step 1: Request Email OTP
    otp_res = client.post("/api/auth/otp/send-email", json={"email": admin_email})
    assert otp_res.status_code == 200
    otp_data = otp_res.json()
    email_otp = otp_data["email_otp"]

    # Step 2: Attempt registration with INCORRECT admin auth code (should fail with 403)
    bad_auth_res = client.post("/api/auth/admin/register", json={
        "name": "Ops Reviewer",
        "email": admin_email,
        "password": "AdminPassword@123",
        "admin_auth_code": "WRONG_SECRET_CODE",
        "email_otp": email_otp,
        "permission_level": "Reviewer",
    })
    assert bad_auth_res.status_code == 403
    assert "Invalid Admin Authentication Code" in bad_auth_res.json()["detail"]

    # Step 3: Register with correct code: SIH2026@DEBUGDYNASTY
    good_res = client.post("/api/auth/admin/register", json={
        "name": "Ops Reviewer",
        "email": admin_email,
        "password": "AdminPassword@123",
        "admin_auth_code": "SIH2026@DEBUGDYNASTY",
        "email_otp": email_otp,
        "permission_level": "Super Admin",
    })
    assert good_res.status_code == 201
    admin_data = good_res.json()
    assert admin_data["role"] == "admin"
    admin_token = admin_data["access_token"]
    assert admin_data["account_info"]["permission_level"] == "Super Admin"

    # Step 4: Admin Login
    login_res = client.post("/api/auth/admin/login", json={
        "email": admin_email,
        "password": "AdminPassword@123",
    })
    assert login_res.status_code == 200
    assert login_res.json()["role"] == "admin"

    # Step 5: Test /admin/me
    me_res = client.get("/api/auth/admin/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == admin_email


def test_strict_role_authorization_guards():
    # 1. Access admin endpoint with NO token -> 401
    no_token_res = client.get("/api/admin/pending-review")
    assert no_token_res.status_code == 401

    # 2. Register user & obtain user token
    user_email = "test.regular.user@example.com"
    otp_res = client.post("/api/auth/otp/send-email", json={"email": user_email}).json()
    reg_user = client.post("/api/auth/user/register", json={
        "name": "Regular User",
        "email": user_email,
        "password": "Password@123",
        "email_otp": otp_res["email_otp"],
        "location": "Delhi, NCR",
    }).json()
    user_token = reg_user["access_token"]

    # 3. Access admin endpoint with USER token -> 403 Forbidden
    user_admin_res = client.get("/api/admin/pending-review", headers={"Authorization": f"Bearer {user_token}"})
    assert user_admin_res.status_code == 403

    # 4. Register admin & obtain admin token
    admin_email = "test.guard.admin@weather.gov.in"
    admin_otp = client.post("/api/auth/otp/send-email", json={"email": admin_email}).json()
    reg_admin = client.post("/api/auth/admin/register", json={
        "name": "Guard Admin",
        "email": admin_email,
        "password": "AdminPassword@123",
        "admin_auth_code": "SIH2026@DEBUGDYNASTY",
        "email_otp": admin_otp["email_otp"],
    }).json()
    admin_token = reg_admin["access_token"]

    # 5. Access admin endpoint with ADMIN token -> 200 OK
    admin_res = client.get("/api/admin/pending-review", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_res.status_code == 200


def test_user_forgot_and_reset_password_flow():
    email = "test.reset.citizen@example.com"
    old_password = "InitialPassword@123"
    new_password = "BrandNewSecurePassword@2026"

    # Step 1: Request forgot-password for non-existent email -> 404
    non_existent = client.post("/api/auth/forgot-password", json={"email": "nonexistent.user@example.com"})
    assert non_existent.status_code == 404
    assert "No registered account found" in non_existent.json()["detail"]

    # Step 2: Register test citizen user
    otp_res = client.post("/api/auth/otp/send-email", json={"email": email}).json()
    reg_res = client.post("/api/auth/user/register", json={
        "name": "Reset Test Citizen",
        "email": email,
        "password": old_password,
        "email_otp": otp_res["email_otp"],
        "location": "Bengaluru, Karnataka",
    })
    assert reg_res.status_code == 201

    # Step 3: Initiate Forgot Password
    forgot_res = client.post("/api/auth/forgot-password", json={"email": email})
    assert forgot_res.status_code == 200
    forgot_data = forgot_res.json()
    assert forgot_data["status"] == "success"
    reset_otp = forgot_data["email_otp"]
    assert len(reset_otp) == 6

    # Step 4: Attempt reset with wrong OTP -> 400 Bad Request
    bad_reset = client.post("/api/auth/reset-password", json={
        "email": email,
        "otp": "999999",
        "new_password": new_password,
    })
    assert bad_reset.status_code == 400
    assert "Invalid or expired OTP" in bad_reset.json()["detail"]

    # Step 5: Reset password with valid OTP and user-chosen new password
    good_reset = client.post("/api/auth/reset-password", json={
        "email": email,
        "otp": reset_otp,
        "new_password": new_password,
    })
    assert good_reset.status_code == 200
    assert good_reset.json()["status"] == "success"

    # Step 6: Verify in DB that the new password is saved and securely HASHED (not plain text)
    db = SessionLocal()
    db_user = db.query(User).filter(User.Email == email).first()
    assert db_user is not None
    assert db_user.Password != new_password
    assert len(db_user.Password) >= 60  # bcrypt / sha256 hash length
    db.close()

    # Step 7: Old password should now fail
    old_login = client.post("/api/auth/user/login", json={
        "email": email,
        "password": old_password,
    })
    assert old_login.status_code == 401

    # Step 8: User can log in with new password
    new_login = client.post("/api/auth/user/login", json={
        "email": email,
        "password": new_password,
    })
    assert new_login.status_code == 200
    assert new_login.json()["role"] == "user"


def test_admin_forgot_and_reset_password_flow():
    admin_email = "test.reset.admin@weather.gov.in"
    old_pw = "OldAdminPass@123"
    new_pw = "SuperSecretAdminPass@2026"

    # Step 1: Register test Admin
    otp_res = client.post("/api/auth/otp/send-email", json={"email": admin_email}).json()
    reg_admin = client.post("/api/auth/admin/register", json={
        "name": "Reset Admin",
        "email": admin_email,
        "password": old_pw,
        "admin_auth_code": "SIH2026@DEBUGDYNASTY",
        "email_otp": otp_res["email_otp"],
    })
    assert reg_admin.status_code == 201

    # Step 2: Forgot password for admin
    forgot_res = client.post("/api/auth/forgot-password", json={"email": admin_email})
    assert forgot_res.status_code == 200
    otp = forgot_res.json()["email_otp"]

    # Step 3: Reset password for admin
    reset_res = client.post("/api/auth/reset-password", json={
        "email": admin_email,
        "otp": otp,
        "new_password": new_pw,
    })
    assert reset_res.status_code == 200

    # Step 4: Verify DB hash for admin
    db = SessionLocal()
    db_admin = db.query(Admin).filter(Admin.Email == admin_email).first()
    assert db_admin is not None
    assert db_admin.Password != new_pw
    db.close()

    # Step 5: Old login fails, new login succeeds
    assert client.post("/api/auth/admin/login", json={"email": admin_email, "password": old_pw}).status_code == 401
    new_login = client.post("/api/auth/admin/login", json={"email": admin_email, "password": new_pw})
    assert new_login.status_code == 200
    assert new_login.json()["role"] == "admin"


def test_admin_role_selection_and_cross_login_prevention():
    # 1. Register a Super Admin
    super_admin_email = "test.role.superadmin@weather.gov.in"
    otp_res = client.post("/api/auth/otp/send-email", json={"email": super_admin_email}).json()
    sa_reg = client.post("/api/auth/admin/register", json={
        "name": "Head Super Admin",
        "email": super_admin_email,
        "password": "SuperSecurePass@123",
        "admin_auth_code": "SIH2026@DEBUGDYNASTY",
        "email_otp": otp_res["email_otp"],
        "permission_level": "Super Admin",
    })
    assert sa_reg.status_code == 201
    assert sa_reg.json()["account_info"]["permission_level"] == "Super Admin"

    # 2. Register a Reviewer
    reviewer_email = "test.role.reviewer@weather.gov.in"
    otp_res_rev = client.post("/api/auth/otp/send-email", json={"email": reviewer_email}).json()
    rev_reg = client.post("/api/auth/admin/register", json={
        "name": "Field Reviewer",
        "email": reviewer_email,
        "password": "ReviewerSecurePass@123",
        "admin_auth_code": "SIH2026@DEBUGDYNASTY",
        "email_otp": otp_res_rev["email_otp"],
        "permission_level": "Reviewer",
    })
    assert rev_reg.status_code == 201
    assert rev_reg.json()["account_info"]["permission_level"] == "Reviewer"

    # 3. Super Admin logs in as 'Super Admin' -> Success (200)
    sa_login_ok = client.post("/api/auth/admin/login", json={
        "email": super_admin_email,
        "password": "SuperSecurePass@123",
        "role": "Super Admin",
    })
    assert sa_login_ok.status_code == 200
    assert sa_login_ok.json()["account_info"]["permission_level"] == "Super Admin"

    # 4. Super Admin attempts to login as 'Reviewer' -> Forbidden (403)
    sa_login_fail = client.post("/api/auth/admin/login", json={
        "email": super_admin_email,
        "password": "SuperSecurePass@123",
        "role": "Reviewer",
    })
    assert sa_login_fail.status_code == 403
    assert "registered as 'Super Admin' and cannot log in as a 'Reviewer'" in sa_login_fail.json()["detail"]

    # 5. Reviewer logs in as 'Reviewer' -> Success (200)
    rev_login_ok = client.post("/api/auth/admin/login", json={
        "email": reviewer_email,
        "password": "ReviewerSecurePass@123",
        "role": "Reviewer",
    })
    assert rev_login_ok.status_code == 200
    assert rev_login_ok.json()["account_info"]["permission_level"] == "Reviewer"

    # 6. Reviewer attempts to login as 'Super Admin' -> Forbidden (403)
    rev_login_fail = client.post("/api/auth/admin/login", json={
        "email": reviewer_email,
        "password": "ReviewerSecurePass@123",
        "role": "Super Admin",
    })
    assert rev_login_fail.status_code == 403
    assert "registered as 'Reviewer' and cannot log in as a 'Super Admin'" in rev_login_fail.json()["detail"]

    # 7. Also test with permission_level alias field
    rev_login_fail_alias = client.post("/api/auth/admin/login", json={
        "email": reviewer_email,
        "password": "ReviewerSecurePass@123",
        "permission_level": "Super Admin",
    })
    assert rev_login_fail_alias.status_code == 403

    # 8. Test invalid role string -> Bad Request (400)
    invalid_role_res = client.post("/api/auth/admin/login", json={
        "email": reviewer_email,
        "password": "ReviewerSecurePass@123",
        "role": "InvalidRole",
    })
    assert invalid_role_res.status_code == 400
    assert "Invalid admin role" in invalid_role_res.json()["detail"]

    # 9. Test require_super_admin dependency guard directly
    from app.api.deps import require_super_admin
    from fastapi import HTTPException

    db = SessionLocal()
    sa_admin = db.query(Admin).filter(Admin.Email == super_admin_email).first()
    rev_admin = db.query(Admin).filter(Admin.Email == reviewer_email).first()

    # Super Admin passes require_super_admin
    assert require_super_admin(admin=sa_admin).Id == sa_admin.Id

    # Reviewer fails require_super_admin with 403
    try:
        require_super_admin(admin=rev_admin)
        assert False, "Reviewer should not pass require_super_admin"
    except HTTPException as e:
        assert e.status_code == 403
        assert "Super Admin privileges required" in e.detail

    db.close()


if __name__ == "__main__":
    print("Running auth flow tests...")
    cleanup_db()
    test_otp_dispatch_and_verification()
    print("[PASS] test_otp_dispatch_and_verification")
    test_resend_otp_and_cooldown_rate_limit()
    print("[PASS] test_resend_otp_and_cooldown_rate_limit")
    test_gps_location_resolution()
    print("[PASS] test_gps_location_resolution")
    test_user_registration_with_gps_location_and_otps()
    print("[PASS] test_user_registration_with_gps_location_and_otps")
    test_admin_registration_with_auth_code_and_otps()
    print("[PASS] test_admin_registration_with_auth_code_and_otps")
    test_strict_role_authorization_guards()
    print("[PASS] test_strict_role_authorization_guards")
    test_user_forgot_and_reset_password_flow()
    print("[PASS] test_user_forgot_and_reset_password_flow")
    test_admin_forgot_and_reset_password_flow()
    print("[PASS] test_admin_forgot_and_reset_password_flow")
    test_admin_role_selection_and_cross_login_prevention()
    print("[PASS] test_admin_role_selection_and_cross_login_prevention")
    cleanup_db()
    print("\nALL AUTH & ROLE SECURITY TESTS PASSED SUCCESSFULLY!")

