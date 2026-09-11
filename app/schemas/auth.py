"""
Pydantic schemas for User & Admin authentication, Email OTP verification, and GPS location resolution.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field


# --- OTP Schemas ---

class SendEmailOtpRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to receive the 6-digit OTP code", example="citizen.user@example.com")


# Alias for general OTP requests
SendOtpRequest = SendEmailOtpRequest


class ResendOtpRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to receive the resent 6-digit OTP code", example="citizen.user@example.com")


# Alias for resend OTP requests
ResendEmailOtpRequest = ResendOtpRequest


class VerifyOtpRequest(BaseModel):
    channel: str = Field("email", description="Channel to verify (defaults to 'email')", example="email")
    identifier: str = Field(..., description="Email address to verify", example="citizen.user@example.com")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code", example="123456")


class OtpResponse(BaseModel):
    status: str = "success"
    message: str
    email: Optional[str] = None
    email_otp: Optional[str] = Field(None, description="Generated OTP (returned for easy Swagger UI testing)")
    expires_in_seconds: int = 600
    cooldown_seconds: Optional[int] = Field(None, description="Cooldown period in seconds before next resend is allowed")


# --- GPS Location Resolution Schema ---

class ResolveLocationRequest(BaseModel):
    latitude: float = Field(..., description="GPS Latitude coordinate", example=19.0760)
    longitude: float = Field(..., description="GPS Longitude coordinate", example=72.8777)


class LocationResolutionResponse(BaseModel):
    status: str = "success"
    latitude: float
    longitude: float
    city: str
    state: str
    formatted_location: str
    distance_km: float = 0.0
    suburb: Optional[str] = Field(None, description="Local suburb, neighbourhood, colony or area", example="Kurla West")
    road: Optional[str] = Field(None, description="Street or road name", example="Shahid Major Kaustubh Rane flyover")
    district: Optional[str] = Field(None, description="District or municipal zone", example="Mumbai Suburban District")
    postcode: Optional[str] = Field(None, description="Postal / PIN code", example="400070")
    full_address: Optional[str] = Field(None, description="Full detailed pinpoint address from OpenStreetMap")
    accuracy: str = Field("pinpoint", description="Resolution accuracy level ('pinpoint' or 'approximate')")


# --- User Registration & Login Schemas ---

class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full Name of the citizen user", example="Aarav Sharma")
    email: EmailStr = Field(..., description="Unique Email address", example="aarav.sharma@example.com")
    password: str = Field(..., min_length=6, max_length=100, description="Account password (min 6 characters)", example="SecurePass@2026")
    email_otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP received via email", example="123456")
    location: Optional[str] = Field(None, description="Manual location description (optional if GPS coordinates provided)", example="Mumbai, Maharashtra")
    latitude: Optional[float] = Field(None, description="GPS Latitude from device location (optional)", example=19.0760)
    longitude: Optional[float] = Field(None, description="GPS Longitude from device location (optional)", example=72.8777)


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Registered Email address", example="aarav.sharma@example.com")
    password: str = Field(..., description="Account password", example="SecurePass@2026")


# --- Admin Registration & Login Schemas ---

class AdminRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full Name of the Administrator / Reviewer", example="Duty Reviewer Officer")
    email: EmailStr = Field(..., description="Official Government / Organization Email", example="reviewer.ops@weather.gov.in")
    password: str = Field(..., min_length=6, max_length=100, description="Admin Password (min 6 characters)", example="AdminSecure@2026")
    admin_auth_code: str = Field(
        ...,
        description="Hardcoded Authentication Secret Code required for Admin creation. Must be: SIH2026@DEBUGDYNASTY",
        example="SIH2026@DEBUGDYNASTY",
    )
    email_otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP received on email", example="123456")
    permission_level: Optional[str] = Field("Reviewer", description="Role level: 'Reviewer' or 'Super Admin'", example="Reviewer")


def normalize_admin_role(role_raw: Optional[str]) -> Optional[str]:
    """
    Normalizes admin role strings to canonical 'Super Admin' or 'Reviewer'.
    Returns None if unrecognized.
    """
    if not role_raw:
        return None
    cleaned = role_raw.strip().lower().replace("_", " ").replace("-", " ")
    if cleaned in ["super admin", "superadmin"]:
        return "Super Admin"
    if cleaned in ["reviewer"]:
        return "Reviewer"
    return None


class AdminLoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Registered Admin Email", example="reviewer.ops@weather.gov.in")
    password: str = Field(..., description="Admin Password", example="AdminSecure@2026")
    role: Optional[str] = Field(
        None,
        description="Selected Admin Role from login panel: 'Super Admin' or 'Reviewer'",
        example="Reviewer",
    )
    permission_level: Optional[str] = Field(
        None,
        description="Alternative field for selected Admin Role: 'Super Admin' or 'Reviewer'",
        example="Reviewer",
    )


# --- Auth Token & Profile Responses ---

class AuthTokenResponse(BaseModel):
    status: str = "success"
    message: str
    access_token: str
    token_type: str = "bearer"
    role: str
    account_info: Dict[str, Any]


# --- Password Reset Schemas ---

class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(
        ...,
        description="Registered account email address to receive the password reset OTP",
        example="aarav.sharma@example.com",
    )


class ResetPasswordRequest(BaseModel):
    email: EmailStr = Field(
        ...,
        description="Registered account email address",
        example="aarav.sharma@example.com",
    )
    otp: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-digit OTP code received on email",
        example="123456",
    )
    new_password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="New account password chosen by user (minimum 6 characters)",
        example="NewSecurePass@2026",
    )


class ResetPasswordResponse(BaseModel):
    status: str = "success"
    message: str
    email: Optional[str] = None

