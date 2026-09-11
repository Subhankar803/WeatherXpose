"""
OTP Generation & Verification Service for Email Authentication.
Dispatches real verification emails via SMTP (Gmail) and caches 6-digit OTPs with 10-minute TTL.
"""
import time
import secrets
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Tuple, Optional

from app.config import settings

logger = logging.getLogger(__name__)

# In-memory thread-safe OTP store: { email: (otp_code, expires_at_timestamp, last_sent_at_timestamp) }
_EMAIL_OTP_STORE: Dict[str, Tuple[str, float, float]] = {}

OTP_EXPIRY_SECONDS = 600  # 10 minutes
DEFAULT_RESEND_COOLDOWN_SECONDS = 30  # 30 seconds cooldown between OTP resends


class OtpRateLimitError(Exception):
    """Raised when OTP generation or resend violates rate limit cooldown."""
    def __init__(self, retry_after: int, message: Optional[str] = None):
        self.retry_after = retry_after
        self.message = message or f"Please wait {retry_after} seconds before requesting a new OTP."
        super().__init__(self.message)


def _generate_6digit_otp() -> str:
    """Generates a secure 6-digit numeric string."""
    return str(secrets.randbelow(900000) + 100000)


def send_real_email_otp(to_email: str, otp: str, purpose: str = "verification") -> bool:
    """
    Connects to the configured SMTP server (Gmail) and delivers a branded HTML & text OTP email.
    """
    host = settings.smtp_host.strip()
    port = settings.smtp_port
    user = settings.smtp_user.strip()
    password = settings.smtp_password.strip()
    from_email = settings.smtp_from_email.strip() or user

    if not host or not user or not password:
        logger.warning(
            f"[OTP_SERVICE] [SMTP Not Fully Configured] Host='{host}', User='{user}'. "
            f"Falling back to console simulation."
        )
        print(f"[Simulated Email Gateway] To: {to_email} | Subject: Verification Code | OTP: {otp}")
        return False

    # Build the MIME Message
    is_resend = "resend" in purpose.lower()
    is_password_reset = "password" in purpose.lower()

    if is_password_reset:
        subject_title = "Password Reset Code"
        badge_title = "Password Reset Verification Code"
        code_desc = "password reset verification code"
        purpose_desc = "password reset"
    elif is_resend:
        subject_title = "Your New Verification Code"
        badge_title = "Your New Single-Use Verification Code"
        code_desc = "new verification code"
        purpose_desc = purpose.replace('_', ' ')
    else:
        subject_title = "Your Verification Code"
        badge_title = "Your Single-Use Verification Code"
        code_desc = "verification code"
        purpose_desc = purpose.replace('_', ' ')

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{subject_title}: {otp} - National Weather Platform"
    msg["From"] = f"National Weather Platform <{from_email}>"
    msg["To"] = to_email

    # Plain-text fallback
    text_content = (
        f"Hello,\n\n"
        f"Your {code_desc} for the National Weather Big Data Platform is: {otp}\n\n"
        f"This code will expire in 10 minutes. If you did not request this code, please ignore this email.\n\n"
        f"Regards,\nNational Weather Platform Team"
    )

    # Rich HTML Body
    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{subject_title}</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0b1120; color: #e2e8f0; margin: 0; padding: 40px 20px;">
  <div style="max-width: 520px; margin: 0 auto; background: #1e293b; border-radius: 12px; border: 1px solid #334155; padding: 32px; box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);">
    <div style="text-align: center; margin-bottom: 24px;">
      <h2 style="color: #38bdf8; margin: 0 0 6px 0; font-size: 22px; font-weight: 700; letter-spacing: -0.5px;">
        National Weather Big Data Platform
      </h2>
      <p style="color: #94a3b8; font-size: 13px; margin: 0;">Ministry of Earth Sciences / IMD Crowdsourced Verification</p>
    </div>
    
    <div style="background-color: #0f172a; border-radius: 8px; border: 1px solid #1e293b; padding: 24px; text-align: center; margin-bottom: 24px;">
      <p style="color: #94a3b8; font-size: 14px; margin-top: 0; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px;">
        {badge_title}
      </p>
      <div style="font-size: 38px; font-weight: 800; letter-spacing: 8px; color: #38bdf8; font-family: monospace; padding: 8px 0;">
        {otp}
      </div>
      <p style="color: #64748b; font-size: 12px; margin: 12px 0 0 0;">Valid for 10 minutes (Expires in 600 seconds)</p>
    </div>

    <p style="color: #cbd5e1; font-size: 14px; line-height: 1.6; margin-bottom: 16px;">
      Use this code to complete your {purpose_desc} on the National Weather Platform. Do not share this code with anyone.
    </p>

    <hr style="border: none; border-top: 1px solid #334155; margin: 24px 0;">

    <p style="color: #64748b; font-size: 11px; text-align: center; margin: 0;">
      If you did not request this email, please ignore it or report to security@weather.gov.in.
    </p>
  </div>
</body>
</html>
"""

    msg.attach(MIMEText(text_content, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    try:
        if port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=12)
        else:
            server = smtplib.SMTP(host, port, timeout=12)
            if settings.smtp_use_tls:
                server.ehlo()
                server.starttls()
                server.ehlo()

        server.login(user, password)
        server.send_message(msg)
        server.quit()
        logger.info(f"[OTP_SERVICE] [REAL_EMAIL_SENT] Successfully delivered OTP to '{to_email}' via {host}:{port}")
        print(f"[Real Email Gateway] Successfully dispatched OTP email to: {to_email}")
        return True
    except Exception as exc:
        logger.error(f"[OTP_SERVICE] [SMTP_ERROR] Failed to send real email to '{to_email}': {exc}", exc_info=True)
        print(f"[SMTP Error] Could not deliver email to {to_email}: {exc}")
        return False


def get_resend_cooldown_remaining(email: str, cooldown_seconds: Optional[int] = None) -> int:
    """
    Returns the remaining cooldown seconds before a new OTP can be requested for this email.
    Returns 0 if no cooldown is active.
    """
    cooldown = (
        cooldown_seconds
        if cooldown_seconds is not None
        else getattr(settings, "otp_resend_cooldown_seconds", DEFAULT_RESEND_COOLDOWN_SECONDS)
    )
    email_clean = email.strip().lower()
    record = _EMAIL_OTP_STORE.get(email_clean)
    if not record or len(record) < 3:
        return 0

    last_sent_at = record[2]
    elapsed = time.time() - last_sent_at
    if elapsed < cooldown:
        return max(1, int(cooldown - elapsed))
    return 0


def generate_email_otp(email: str, purpose: str = "registration") -> str:
    """
    Generates, caches, and dispatches a 6-digit OTP to the given email address.
    """
    email_clean = email.strip().lower()
    otp = _generate_6digit_otp()
    now = time.time()
    expiry = getattr(settings, "otp_expiry_seconds", OTP_EXPIRY_SECONDS)
    expires_at = now + expiry
    _EMAIL_OTP_STORE[email_clean] = (otp, expires_at, now)

    logger.info(f"[OTP_SERVICE] Generated OTP for '{email_clean}' (Purpose: {purpose}, TTL: {expiry}s)")
    
    # Send actual email through SMTP
    send_real_email_otp(email_clean, otp, purpose=purpose)
    
    return otp


def resend_email_otp(
    email: str,
    purpose: str = "resend_verification",
    cooldown_seconds: Optional[int] = None,
) -> Tuple[str, int]:
    """
    Resends a fresh 6-digit OTP to the given email address after enforcing cooldown rate limits.
    Invalidates any previous OTP for this email and resets the expiry timer.
    
    Raises:
        OtpRateLimitError: If called before cooldown_seconds have elapsed since last send.
        
    Returns:
        Tuple[str, int]: (new_otp, expires_in_seconds)
    """
    email_clean = email.strip().lower()
    remaining = get_resend_cooldown_remaining(email_clean, cooldown_seconds=cooldown_seconds)
    if remaining > 0:
        raise OtpRateLimitError(
            retry_after=remaining,
            message=f"Please wait {remaining} seconds before requesting a new OTP."
        )

    otp = _generate_6digit_otp()
    now = time.time()
    expiry = getattr(settings, "otp_expiry_seconds", OTP_EXPIRY_SECONDS)
    expires_at = now + expiry
    _EMAIL_OTP_STORE[email_clean] = (otp, expires_at, now)

    logger.info(f"[OTP_SERVICE] Resent fresh OTP for '{email_clean}' (Purpose: {purpose}, TTL: {expiry}s)")
    send_real_email_otp(email_clean, otp, purpose=purpose)
    return otp, expiry


def verify_email_otp(email: str, otp: str, consume: bool = True) -> bool:
    """
    Verifies if the provided OTP matches the active unexpired OTP for the email.
    If consume=True, invalidates the OTP upon successful verification.
    """
    email_clean = email.strip().lower()
    record = _EMAIL_OTP_STORE.get(email_clean)
    if not record:
        return False

    cached_otp = record[0]
    expires_at = record[1]
    if time.time() > expires_at:
        _EMAIL_OTP_STORE.pop(email_clean, None)
        return False

    if cached_otp == otp.strip():
        if consume:
            _EMAIL_OTP_STORE.pop(email_clean, None)
        return True

    return False

