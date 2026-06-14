"""
Authentication module.
Handles demo user login and JWT token creation/verification.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status
from app.config import settings

# ─── Demo Users ─────────────────────────────────────────
# Plain password comparison (avoids bcrypt/passlib version conflicts)
# In production, use proper hashed passwords.

DEMO_USERS = {
    "dr.mehta":     {"username": "dr.mehta",     "role": "doctor",            "password": "doctor123"},
    "nurse.priya":  {"username": "nurse.priya",  "role": "nurse",             "password": "nurse123"},
    "billing.ravi": {"username": "billing.ravi", "role": "billing_executive", "password": "billing123"},
    "tech.anand":   {"username": "tech.anand",   "role": "technician",        "password": "tech123"},
    "admin.sys":    {"username": "admin.sys",     "role": "admin",             "password": "admin123"},
}


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Return user dict if credentials are valid, else None."""
    user = DEMO_USERS.get(username)
    if not user:
        return None
    if password != user["password"]:
        return None
    return user


def create_access_token(data: dict) -> str:
    """Create a JWT token with expiry."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token. Raises HTTPException if invalid."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        if not username or not role:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return {"username": username, "role": role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
