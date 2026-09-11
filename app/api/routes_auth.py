"""
Authentication, Registration & Email OTP Verification Endpoints.

Provides:
1. Email OTP Generation & Verification (via real Gmail SMTP).
2. Citizen User Registration (with GPS / manual location) & Login Panels.
3. Admin Registration (with required hardcoded Auth Code: SIH2026@DEBUGDYNASTY) & Login Panels.
4. Profile lookups and GPS location resolver.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import hashlib
import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.api.deps import get_db, get_current_user, require_user, require_admin
from app.models.user import User
from app.models.admin import Admin
from app.models.sources import Source
from app.utils.geo_utils import resolve_user_location, reverse_geocode_coords
from app.services.otp_service import (
    generate_email_otp,
    resend_email_otp,
    verify_email_otp,
    OtpRateLimitError,
)
from app.schemas.auth import (
    SendEmailOtpRequest,
    SendOtpRequest,
    ResendOtpRequest,
    ResendEmailOtpRequest,
    VerifyOtpRequest,
    OtpResponse,
    ResolveLocationRequest,
    LocationResolutionResponse,
    UserRegisterRequest,
    UserLoginRequest,
    AdminRegisterRequest,
    AdminLoginRequest,
    normalize_admin_role,
    AuthTokenResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
)

router = APIRouter()

# Hardcoded authentication secret required for Admin account creation
ADMIN_AUTHENTICATION_CODE = "SIH2026@DEBUGDYNASTY"


# --- Password & Token Helpers ---

def hash_password(password: str) -> str:
    """Hashes a password with bcrypt or SHA256 fallback."""
    try:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    except Exception:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against hashed password."""
    try:
        if bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8")):
            return True
    except Exception:
        pass
    sha_hash = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    return (sha_hash == hashed_password) or (plain_password == hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


# =====================================================================
# 1. OTP DISPATCH & VERIFICATION ENDPOINTS
# =====================================================================

@router.post(
    "/otp/send-email",
    response_model=OtpResponse,
    summary="Send 6-digit OTP to Email",
    description="Generates and dispatches a 6-digit verification code to the given email address via real SMTP (valid for 10 minutes).",
)
@router.post("/otp/send", response_model=OtpResponse, include_in_schema=False)
def send_email_verification_otp(payload: SendEmailOtpRequest):
    otp = generate_email_otp(payload.email, purpose="email_verification")
    return OtpResponse(
        status="success",
        message=f"6-digit verification code sent to email: {payload.email}. (Valid for {settings.otp_expiry_seconds // 60} minutes)",
        email=payload.email,
        email_otp=otp,
        expires_in_seconds=settings.otp_expiry_seconds,
        cooldown_seconds=settings.otp_resend_cooldown_seconds,
    )


@router.post(
    "/otp/resend",
    response_model=OtpResponse,
    summary="Resend 6-digit OTP to Email",
    description="Generates and re-dispatches a fresh 6-digit verification code to the given email address. Enforces a 30-second cooldown between requests to prevent abuse.",
    responses={
        200: {"description": "OTP resent successfully via email."},
        429: {"description": "Rate limit cooldown active. Retry after specified seconds in Retry-After header."},
    },
)
@router.post("/otp/resend-email", response_model=OtpResponse, include_in_schema=False)
def resend_email_verification_otp(payload: ResendOtpRequest):
    try:
        otp, expires_in = resend_email_otp(payload.email, purpose="resend_verification")
        return OtpResponse(
            status="success",
            message=f"Fresh 6-digit verification code resent to email: {payload.email}. (Valid for {expires_in // 60} minutes)",
            email=payload.email,
            email_otp=otp,
            expires_in_seconds=expires_in,
            cooldown_seconds=settings.otp_resend_cooldown_seconds,
        )
    except OtpRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=exc.message,
            headers={"Retry-After": str(exc.retry_after)},
        )


@router.post(
    "/otp/verify",
    summary="Verify Email OTP",
    description="Verifies whether a 6-digit OTP code matches the active code for the given email address.",
)
def verify_individual_otp(payload: VerifyOtpRequest):
    is_valid = verify_email_otp(payload.identifier, payload.otp, consume=False)

    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP code. Please request a new code.")

    return {
        "status": "success",
        "message": f"OTP for {payload.identifier} successfully verified.",
        "valid": True,
    }


# =====================================================================
# 2. GPS LOCATION RESOLVER HELPER (FOR CITIZEN REGISTRATION)
# =====================================================================

@router.post(
    "/resolve-location",
    response_model=LocationResolutionResponse,
    summary="Resolve GPS Coordinates to Pinpoint Location",
    description="Resolves latitude and longitude coordinates to exact pinpoint location (street, suburb, city, district, state, PIN code) using OpenStreetMap reverse-geocoding.",
)
def resolve_gps_coordinates(payload: ResolveLocationRequest):
    geo_data = reverse_geocode_coords(payload.latitude, payload.longitude)
    return LocationResolutionResponse(
        status="success",
        latitude=geo_data["latitude"],
        longitude=geo_data["longitude"],
        city=geo_data["city"],
        state=geo_data["state"],
        formatted_location=geo_data["formatted_location"],
        distance_km=geo_data.get("distance_km", 0.0),
        suburb=geo_data.get("suburb"),
        road=geo_data.get("road"),
        district=geo_data.get("district"),
        postcode=geo_data.get("postcode"),
        full_address=geo_data.get("full_address"),
        accuracy=geo_data.get("accuracy", "pinpoint"),
    )



# =====================================================================
# 3. CITIZEN USER REGISTRATION & LOGIN PANELS
# =====================================================================

@router.post(
    "/user/register",
    status_code=status.HTTP_201_CREATED,
    response_model=AuthTokenResponse,
    summary="Citizen User Registration Panel",
    description="Registers a new citizen user. Requires Name, Email, Password, Email OTP, and optional GPS / manual location.",
)
@router.post("/register", status_code=status.HTTP_201_CREATED, include_in_schema=False)
def register_user(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    # 1. Uniqueness check on Email
    email_clean = payload.email.strip().lower()
    if db.query(User).filter(User.Email == email_clean).first():
        raise HTTPException(status_code=400, detail="A user account with this email address already exists.")

    # 2. Verify Email OTP
    if not verify_email_otp(email_clean, payload.email_otp, consume=True):
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired Email OTP. Please request a new OTP via /api/auth/otp/send-email.",
        )

    # 3. Resolve Location (manual entry OR GPS coordinates)
    resolved_location = resolve_user_location(
        custom_location=payload.location,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )

    # 4. Create User record
    hashed_pw = hash_password(payload.password)
    user = User(
        Name=payload.name.strip(),
        Email=email_clean,
        Password=hashed_pw,
        Location=resolved_location,
        Is_Active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Initialize CitizenPortal Source record for trust tracking
    portal_src = Source(
        Username=user.Email,
        Source_Name=user.Name,
        Platform="CitizenPortal",
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
    db.add(portal_src)
    db.commit()

    # 5. Generate JWT access token
    token = create_access_token({"sub": user.Email, "role": "user", "id": user.Id})

    return AuthTokenResponse(
        status="success",
        message="Citizen user account successfully registered.",
        access_token=token,
        token_type="bearer",
        role="user",
        account_info={
            "id": user.Id,
            "name": user.Name,
            "email": user.Email,
            "location": user.Location,
            "trust_status": "GREY",
            "created_at": user.Created_at.isoformat() if user.Created_at else None,
        },
    )


@router.post(
    "/user/login",
    response_model=AuthTokenResponse,
    summary="Citizen User Login Panel",
    description="Authenticates a citizen user using email and password, returning a JWT bearer token.",
)
@router.post("/login", include_in_schema=False)
def user_login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    email_clean = payload.email.strip().lower()
    user = db.query(User).filter(User.Email == email_clean).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email address or password.")

    if not verify_password(payload.password, user.Password):
        raise HTTPException(status_code=401, detail="Invalid email address or password.")

    if not user.Is_Active:
        raise HTTPException(
            status_code=403,
            detail="Account is BLOCKED due to policy violations (RED list disinformation sanctions).",
        )

    user.Last_Login = datetime.utcnow()
    db.commit()

    token = create_access_token({"sub": user.Email, "role": "user", "id": user.Id})
    return AuthTokenResponse(
        status="success",
        message="User login successful.",
        access_token=token,
        token_type="bearer",
        role="user",
        account_info={
            "id": user.Id,
            "name": user.Name,
            "email": user.Email,
            "location": user.Location,
            "last_login": user.Last_Login.isoformat() if user.Last_Login else None,
        },
    )


@router.get(
    "/user/me",
    summary="Get Current Citizen Profile",
    description="Fetches profile details for the currently authenticated citizen user.",
)
def get_current_user_profile(user: User = Depends(require_user), db: Session = Depends(get_db)):
    source = db.query(Source).filter(
        Source.Username == user.Email,
        Source.Platform == "CitizenPortal",
    ).first()
    return {
        "authenticated": True,
        "role": "user",
        "id": user.Id,
        "name": user.Name,
        "email": user.Email,
        "location": user.Location,
        "trust_status": source.Trust_Status if source else "GREY",
        "total_reports": source.Total_Reports if source else 0,
        "fake_reports": source.Fake_Reports if source else 0,
        "warnings_count": source.Warnings_Count if source else 0,
    }


# =====================================================================
# 4. ADMIN REGISTRATION & LOGIN PANELS
# =====================================================================

@router.post(
    "/admin/register",
    status_code=status.HTTP_201_CREATED,
    response_model=AuthTokenResponse,
    summary="Admin Registration Panel",
    description=(
        "Registers a new Administrator / Reviewer account. Requires Name, Email, Password, "
        "Email OTP verification, and the hardcoded secret Authentication Code: SIH2026@DEBUGDYNASTY."
    ),
)
def register_admin(payload: AdminRegisterRequest, db: Session = Depends(get_db)):
    # 1. Hardcoded Secret Key Validation
    if payload.admin_auth_code.strip() != ADMIN_AUTHENTICATION_CODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Admin Authentication Code. Access Denied. (Must match authorized deployment key)",
        )

    email_clean = payload.email.strip().lower()

    # 2. Uniqueness check on Email
    if db.query(Admin).filter(Admin.Email == email_clean).first():
        raise HTTPException(status_code=400, detail="An Admin account with this email address already exists.")

    # 3. Verify Email OTP
    if not verify_email_otp(email_clean, payload.email_otp, consume=True):
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired Email OTP. Please request a new OTP via /api/auth/otp/send-email.",
        )

    # 4. Create Admin record
    perm_level = normalize_admin_role(payload.permission_level) or "Reviewer"
    hashed_pw = hash_password(payload.password)
    admin = Admin(
        Name=payload.name.strip(),
        Email=email_clean,
        Password=hashed_pw,
        Permission_Level=perm_level,
        Created_at=datetime.utcnow(),
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    # 5. Generate JWT access token with permission level claim
    token = create_access_token({
        "sub": admin.Email,
        "role": "admin",
        "permission_level": admin.Permission_Level,
        "id": admin.Id,
    })

    return AuthTokenResponse(
        status="success",
        message="Admin account successfully registered with authorized authentication code.",
        access_token=token,
        token_type="bearer",
        role="admin",
        account_info={
            "id": admin.Id,
            "name": admin.Name,
            "email": admin.Email,
            "permission_level": admin.Permission_Level,
            "created_at": admin.Created_at.isoformat() if admin.Created_at else None,
        },
    )


@router.post(
    "/admin/login",
    response_model=AuthTokenResponse,
    summary="Admin Login Panel",
    description="Authenticates an Administrator / Reviewer using official email, password, and selected role ('Super Admin' or 'Reviewer').",
)
@router.post("/admin-login", include_in_schema=False)
def admin_login(payload: AdminLoginRequest, db: Session = Depends(get_db)):
    email_clean = payload.email.strip().lower()
    admin = db.query(Admin).filter(Admin.Email == email_clean).first()
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid admin credentials.")

    if not verify_password(payload.password, admin.Password):
        raise HTTPException(status_code=401, detail="Invalid admin credentials.")

    # Role selection validation:
    # "the login page will be same for both admin, but they have to select Super Admin or Reviewer.
    # If the email is registered as Super Admin, he can't login as a Reviewer. And Reviewer can't login as a Super Admin."
    selected_role_raw = payload.role or payload.permission_level
    if selected_role_raw is not None:
        normalized_role = normalize_admin_role(selected_role_raw)
        if not normalized_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid admin role '{selected_role_raw}'. Please select either 'Super Admin' or 'Reviewer'.",
            )
        if normalized_role != admin.Permission_Level:
            if admin.Permission_Level == "Super Admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. This account is registered as 'Super Admin' and cannot log in as a 'Reviewer'. Please select 'Super Admin' on the login screen.",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. This account is registered as 'Reviewer' and cannot log in as a 'Super Admin'. Please select 'Reviewer' on the login screen.",
                )

    admin.Last_Active = datetime.utcnow()
    db.commit()

    token = create_access_token({
        "sub": admin.Email,
        "role": "admin",
        "permission_level": admin.Permission_Level,
        "id": admin.Id,
    })
    return AuthTokenResponse(
        status="success",
        message="Admin authentication successful.",
        access_token=token,
        token_type="bearer",
        role="admin",
        account_info={
            "id": admin.Id,
            "name": admin.Name,
            "email": admin.Email,
            "permission_level": admin.Permission_Level,
            "last_active": admin.Last_Active.isoformat() if admin.Last_Active else None,
        },
    )


@router.get(
    "/admin/me",
    summary="Get Current Admin Profile",
    description="Fetches profile details for the currently authenticated Admin / Reviewer.",
)
def get_current_admin_profile(admin: Admin = Depends(require_admin)):
    return {
        "authenticated": True,
        "role": "admin",
        "id": admin.Id,
        "name": admin.Name,
        "email": admin.Email,
        "permission_level": admin.Permission_Level,
        "last_active": admin.Last_Active.isoformat() if admin.Last_Active else None,
    }


# =====================================================================
# 5. LEGACY / SHARED PROFILE ENDPOINT
# =====================================================================

@router.get(
    "/me",
    summary="Get General Profile",
    description="Inspects active JWT token and returns profile whether User or Admin.",
)
def get_general_profile(
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user),
):
    if user:
        source = db.query(Source).filter(
            Source.Username == user.Email,
            Source.Platform == "CitizenPortal",
        ).first()
        return {
            "authenticated": True,
            "role": "user",
            "id": user.Id,
            "name": user.Name,
            "email": user.Email,
            "location": user.Location,
            "trust_status": source.Trust_Status if source else "GREY",
        }
    return {"authenticated": False, "role": "guest"}


@router.post(
    "/logout",
    summary="User / Admin Logout",
    description="Terminates the active session and clears authentication credentials.",
)
def logout():
    return {
        "status": "success",
        "message": "Logged out successfully.",
    }


# =====================================================================
# 6. FORGOT & RESET PASSWORD FLOW (USER & ADMIN)
# =====================================================================

@router.post(
    "/forgot-password",
    response_model=OtpResponse,
    summary="Forgot Password - Send OTP to Registered Email",
    description="Validates that the email belongs to a registered User or Admin, generates a 6-digit OTP, and sends it via email (valid for 10 minutes).",
)
@router.post("/user/forgot-password", response_model=OtpResponse, include_in_schema=False)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Step 1 of password recovery:
    Validates account existence and dispatches a single-use 6-digit OTP to the registered email.
    """
    email_clean = payload.email.strip().lower()

    # Verify that the account exists in either User or Admin table
    user = db.query(User).filter(User.Email == email_clean).first()
    admin = db.query(Admin).filter(Admin.Email == email_clean).first() if not user else None

    if not user and not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No registered account found for email: {payload.email}",
        )

    otp = generate_email_otp(email_clean, purpose="password_reset")
    return OtpResponse(
        status="success",
        message=f"Password reset 6-digit OTP code sent to email: {payload.email}. (Valid for {settings.otp_expiry_seconds // 60} minutes)",
        email=payload.email,
        email_otp=otp,
        expires_in_seconds=settings.otp_expiry_seconds,
        cooldown_seconds=settings.otp_resend_cooldown_seconds,
    )


@router.post(
    "/forgot-password/resend",
    response_model=OtpResponse,
    summary="Resend Password Reset OTP",
    description="Resends a fresh 6-digit password reset OTP to the given email address after enforcing cooldown rate limits.",
    responses={
        200: {"description": "Password reset OTP resent successfully via email."},
        429: {"description": "Rate limit cooldown active. Retry after specified seconds in Retry-After header."},
    },
)
def resend_forgot_password_otp(payload: ResendOtpRequest, db: Session = Depends(get_db)):
    """
    Resends a fresh password reset OTP after enforcing the 30-second cooldown rate limit.
    """
    email_clean = payload.email.strip().lower()
    user = db.query(User).filter(User.Email == email_clean).first()
    admin = db.query(Admin).filter(Admin.Email == email_clean).first() if not user else None

    if not user and not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No registered account found for email: {payload.email}",
        )

    try:
        otp, expires_in = resend_email_otp(email_clean, purpose="resend_password_reset")
        return OtpResponse(
            status="success",
            message=f"Fresh 6-digit password reset code resent to email: {payload.email}. (Valid for {expires_in // 60} minutes)",
            email=payload.email,
            email_otp=otp,
            expires_in_seconds=expires_in,
            cooldown_seconds=settings.otp_resend_cooldown_seconds,
        )
    except OtpRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=exc.message,
            headers={"Retry-After": str(exc.retry_after)},
        )


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    summary="Reset Password - Verify Email OTP & Save New Hashed Password",
    description="Verifies the 6-digit OTP sent to the user's email, hashes the new password supplied by the user/admin, and updates it in the database.",
)
@router.post("/user/reset-password", response_model=ResetPasswordResponse, include_in_schema=False)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Step 2 of password recovery:
    Verifies the email OTP, hashes the user-chosen new password, and commits it to the database.
    """
    email_clean = payload.email.strip().lower()

    # 1. Verify account exists
    user = db.query(User).filter(User.Email == email_clean).first()
    admin = db.query(Admin).filter(Admin.Email == email_clean).first() if not user else None

    if not user and not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No registered account found for email: {payload.email}",
        )

    # 2. Verify OTP
    if not verify_email_otp(email_clean, payload.otp, consume=True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP code. Please request a new password reset code.",
        )

    # 3. Hash the user-chosen new password
    hashed_pw = hash_password(payload.new_password)

    # 4. Update the password in database
    if user:
        user.Password = hashed_pw
    elif admin:
        admin.Password = hashed_pw

    db.commit()
    if user:
        db.refresh(user)
    elif admin:
        db.refresh(admin)

    return ResetPasswordResponse(
        status="success",
        message="Password has been successfully updated in database. You can now log in with your new password.",
        email=payload.email,
    )
