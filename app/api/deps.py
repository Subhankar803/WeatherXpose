"""
FastAPI Dependencies: DB session injection & Role-Based JWT authentication using PyJWT.
Strictly verifies roles without any hardcoded fallback.
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database_setup import SessionLocal
from app.models.user import User
from app.models.admin import Admin

bearer_scheme = HTTPBearer(auto_error=False)


def get_token(auth: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)) -> Optional[str]:
    """Extracts the bearer token string from HTTP Authorization header."""
    return auth.credentials if auth else None


# Backward-compatible alias
oauth2_scheme = get_token


def get_db() -> Generator:
    """Provides transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[User]:
    """
    Decodes JWT and returns current User if token is valid and corresponds to a citizen user.
    Returns None if no token or invalid token is supplied (for optional user endpoints).
    """
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if not email or role != "user":
            return None
    except Exception:
        return None

    user = db.query(User).filter(User.Email == email).first()
    return user


def require_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
) -> User:
    """
    Strictly verifies that the request originates from an authenticated Citizen User.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User authentication required. Please login as a citizen user.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if not email or role != "user":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Citizen user permissions required for this resource.",
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired user session token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.Email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found.")
    if not user.Is_Active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is blocked due to policy violations.")
    return user


def require_admin(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
) -> Admin:
    """
    Strictly verifies that the request originates from an authorized Admin / Reviewer.
    No automatic fallback is permitted.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required. Please provide a valid admin bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if role != "admin" or not email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin privileges required.",
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired admin session token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    admin = db.query(Admin).filter(Admin.Email == email).first()
    if not admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin account not found.")
    return admin


def require_super_admin(
    admin: Admin = Depends(require_admin),
) -> Admin:
    """
    Strictly verifies that the request originates from an authorized Super Admin.
    Rejects Reviewers with HTTP 403 Forbidden.
    """
    if admin.Permission_Level != "Super Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin privileges required for this resource.",
        )
    return admin


def require_reviewer(
    admin: Admin = Depends(require_admin),
) -> Admin:
    """
    Verifies that the request originates from an Admin with at least Reviewer privileges
    (both Reviewer and Super Admin are permitted).
    """
    if admin.Permission_Level not in ["Reviewer", "Super Admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reviewer privileges required for this resource.",
        )
    return admin
