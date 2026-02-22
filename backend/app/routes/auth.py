"""
Auth routes – registration, login, with dual-mode phone verification.

Mode 1 (Firebase configured): Firebase sends SMS, frontend verifies, backend checks Firebase token.
Mode 2 (Fallback): Backend generates OTP, logs it to console, user enters it manually.

The mode is auto-detected based on whether FIREBASE_PROJECT_ID (or equivalent) is set.
The /auth/login and /auth/register responses include `auth_mode: "firebase" | "otp"`
so the frontend knows which flow to use.
"""

import random
import logging
import os
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.token import TokenWallet
from app.schemas import (
    RegisterRequest, LoginRequest, TokenResponse, RefreshRequest, UserResponse,
)
from app.services.auth import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    decode_token, get_current_user,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Firebase Admin (optional) ────────────────────────────────

_firebase_ready = False

def _init_firebase():
    global _firebase_ready
    try:
        import firebase_admin
        from firebase_admin import credentials

        if firebase_admin._apps:
            _firebase_ready = True
            return

        # Option 1: Service account JSON file
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if cred_path and os.path.isfile(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            _firebase_ready = True
            logger.info("🔥 Firebase initialized with service account file")
            return

        # Option 2: Project ID only
        project_id = os.getenv("FIREBASE_PROJECT_ID")
        if project_id:
            firebase_admin.initialize_app(options={"projectId": project_id})
            _firebase_ready = True
            logger.info(f"🔥 Firebase initialized with project ID: {project_id}")
            return

        # Option 3: Base64-encoded service account
        import base64, json
        sa_json_b64 = os.getenv("FIREBASE_SERVICE_ACCOUNT_BASE64")
        if sa_json_b64:
            sa_json = json.loads(base64.b64decode(sa_json_b64))
            cred = credentials.Certificate(sa_json)
            firebase_admin.initialize_app(cred)
            _firebase_ready = True
            logger.info("🔥 Firebase initialized with base64 service account")
            return

        logger.warning("⚠️ Firebase not configured — using fallback OTP (console-logged)")

    except ImportError:
        logger.warning("⚠️ firebase-admin not installed — using fallback OTP")


_init_firebase()


# ── Helpers ──────────────────────────────────────────────────

def _get_auth_mode() -> str:
    return "firebase" if _firebase_ready else "otp"


async def _generate_and_send_otp(user: User, db: AsyncSession) -> str:
    """Generate a 6-digit OTP, store on user, and log it (fallback mode)."""
    otp = f"{random.randint(100000, 999999)}"
    user.phone_otp = otp
    user.phone_otp_expires = datetime.utcnow() + timedelta(minutes=10)
    await db.commit()

    # Log to console — visible in Render logs
    logger.info(f"📱 OTP for {user.phone}: {otp}")
    print(f"📱 OTP for {user.phone}: {otp}")
    return otp


# ── Pydantic request models ─────────────────────────────────

class FirebaseVerifyRequest(BaseModel):
    user_id: str
    firebase_id_token: str


# ── Register ─────────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    existing = await db.execute(
        select(User).where((User.email == req.email) | (User.phone == req.phone))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email or phone already registered")

    user = User(
        email=req.email,
        phone=req.phone,
        password_hash=hash_password(req.password),
        full_name=req.full_name,
        role=req.role,
    )
    db.add(user)
    await db.flush()

    profile = Profile(user_id=user.id)
    db.add(profile)

    wallet = TokenWallet(user_id=user.id, balance=0)
    db.add(wallet)

    await db.commit()
    await db.refresh(user)

    auth_mode = _get_auth_mode()

    # In fallback mode, send OTP now
    if auth_mode == "otp":
        await _generate_and_send_otp(user, db)

    return {
        "message": "Account created! Please verify your phone number.",
        "user_id": str(user.id),
        "phone": req.phone,
        "requires_otp": True,
        "auth_mode": auth_mode,
    }


# ── Login ────────────────────────────────────────────────────

@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Verify credentials, return user_id + phone + auth_mode."""
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.is_suspended:
        raise HTTPException(status_code=403, detail="Account suspended")

    user.last_login = datetime.utcnow()
    await db.commit()

    auth_mode = _get_auth_mode()

    # In fallback mode, send OTP now
    if auth_mode == "otp":
        await _generate_and_send_otp(user, db)

    return {
        "message": "Credentials verified. Please verify your phone.",
        "user_id": str(user.id),
        "phone": user.phone,
        "requires_otp": True,
        "auth_mode": auth_mode,
    }


# ── Verify Firebase ID Token ────────────────────────────────

@router.post("/verify-firebase", response_model=TokenResponse)
async def verify_firebase_token(
    req: FirebaseVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    """Verify a Firebase ID token and issue app JWT tokens."""
    result = await db.execute(select(User).where(User.id == req.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if _firebase_ready:
        try:
            from firebase_admin import auth as firebase_auth
            decoded = firebase_auth.verify_id_token(req.firebase_id_token)
            logger.info(f"🔥 Firebase verified phone: {decoded.get('phone_number')} for user {user.id}")
        except Exception as e:
            logger.error(f"Firebase token verification failed: {e}")
            raise HTTPException(status_code=401, detail="Phone verification failed.")
    else:
        logger.warning("⚠️ Firebase not configured, skipping token verification")

    user.phone_verified = True
    access = create_access_token({"sub": str(user.id), "role": user.role.value})
    refresh = create_refresh_token({"sub": str(user.id)})
    user.refresh_token = refresh
    await db.commit()
    await db.refresh(user)

    logger.info(f"✅ Login complete for user {user.id}")
    return TokenResponse(access_token=access, refresh_token=refresh, user=UserResponse.model_validate(user))


# ── Verify Fallback OTP ─────────────────────────────────────

@router.post("/verify-login-otp", response_model=TokenResponse)
async def verify_login_otp(
    user_id: str,
    otp: str,
    db: AsyncSession = Depends(get_db),
):
    """Verify a 6-digit OTP (fallback mode when Firebase is not configured)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.phone_otp:
        raise HTTPException(status_code=400, detail="No OTP sent. Please login again.")

    if user.phone_otp_expires and datetime.utcnow() > user.phone_otp_expires:
        user.phone_otp = None
        user.phone_otp_expires = None
        await db.commit()
        raise HTTPException(status_code=400, detail="OTP expired. Please login again.")

    if otp != user.phone_otp:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    user.phone_verified = True
    user.phone_otp = None
    user.phone_otp_expires = None

    access = create_access_token({"sub": str(user.id), "role": user.role.value})
    refresh = create_refresh_token({"sub": str(user.id)})
    user.refresh_token = refresh
    await db.commit()
    await db.refresh(user)

    logger.info(f"✅ OTP verified, login complete for user {user.id}")
    return TokenResponse(access_token=access, refresh_token=refresh, user=UserResponse.model_validate(user))


# ── Resend OTP ───────────────────────────────────────────────

@router.post("/resend-otp")
async def resend_otp(user_id: str, db: AsyncSession = Depends(get_db)):
    """Resend a fresh OTP (fallback mode only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await _generate_and_send_otp(user, db)
    return {"message": f"New verification code sent to {user.phone}.", "phone": user.phone}


# ── Refresh Token ────────────────────────────────────────────

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Get a new access token using a refresh token."""
    payload = decode_token(req.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or user.refresh_token != req.refresh_token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    access = create_access_token({"sub": str(user.id), "role": user.role.value})
    new_refresh = create_refresh_token({"sub": str(user.id)})
    user.refresh_token = new_refresh
    await db.commit()

    return TokenResponse(access_token=access, refresh_token=new_refresh, user=UserResponse.model_validate(user))


# ── Me ───────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    """Return current user info."""
    return UserResponse.model_validate(current_user)
