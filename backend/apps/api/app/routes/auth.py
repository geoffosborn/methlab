"""Authentication routes — JWT-based, multi-tenant."""

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr

from app.config import get_settings
from app.database import db_execute, db_execute_returning

router = APIRouter(prefix="/auth", tags=["auth"])

# JWT config — key from env or generated at startup
JWT_SECRET = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = JWT_EXPIRY_HOURS * 3600
    user: dict


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str | None
    role: str


def hash_password(password: str) -> str:
    """Hash password with PBKDF2-HMAC-SHA256."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return salt.hex() + ":" + key.hex()


def verify_password(password: str, stored: str) -> bool:
    """Verify password against stored hash."""
    salt_hex, key_hex = stored.split(":")
    salt = bytes.fromhex(salt_hex)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return hmac.compare_digest(key.hex(), key_hex)


def create_token(user_id: int, email: str, role: str) -> str:
    """Create JWT access token."""
    exp = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "exp": exp,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(request: Request) -> dict | None:
    """Extract and verify current user from Authorization header."""
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        return None

    token = auth[7:]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {
            "id": int(payload["sub"]),
            "email": payload["email"],
            "role": payload["role"],
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")


def require_auth(request: Request) -> dict:
    """Dependency: require authenticated user."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(401, "Authentication required")
    return user


def require_admin(request: Request) -> dict:
    """Dependency: require admin role."""
    user = require_auth(request)
    if user["role"] != "admin":
        raise HTTPException(403, "Admin access required")
    return user


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    """Register a new user."""
    # Check if email exists
    existing = db_execute(
        "SELECT id FROM users WHERE email = %s", [req.email], fetch="one"
    )
    if existing:
        raise HTTPException(400, "Email already registered")

    pw_hash = hash_password(req.password)
    user = db_execute_returning(
        """
        INSERT INTO users (email, password_hash, full_name, role)
        VALUES (%s, %s, %s, 'viewer')
        RETURNING id, email, full_name, role
        """,
        [req.email, pw_hash, req.full_name],
    )

    token = create_token(user["id"], user["email"], user["role"])

    return TokenResponse(
        access_token=token,
        user=user,
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """Authenticate and return JWT token."""
    user = db_execute(
        "SELECT id, email, full_name, role, password_hash FROM users WHERE email = %s",
        [req.email],
        fetch="one",
    )

    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(401, "Invalid email or password")

    if not user.get("is_active", True):
        raise HTTPException(403, "Account is disabled")

    token = create_token(user["id"], user["email"], user["role"])

    return TokenResponse(
        access_token=token,
        user={
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
        },
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(require_auth)):
    """Get current authenticated user."""
    db_user = db_execute(
        "SELECT id, email, full_name, role FROM users WHERE id = %s",
        [user["id"]],
        fetch="one",
    )
    if not db_user:
        raise HTTPException(404, "User not found")
    return UserResponse(**db_user)


@router.get("/facilities")
async def get_user_facilities(user: dict = Depends(require_auth)):
    """Get facilities the current user has access to."""
    if user["role"] == "admin":
        # Admins see all facilities
        rows = db_execute(
            "SELECT id, name, state FROM facilities ORDER BY name"
        )
    else:
        rows = db_execute(
            """
            SELECT f.id, f.name, f.state, ufa.access_level
            FROM user_facility_access ufa
            JOIN facilities f ON f.id = ufa.facility_id
            WHERE ufa.user_id = %s
            ORDER BY f.name
            """,
            [user["id"]],
        )

    return rows or []
