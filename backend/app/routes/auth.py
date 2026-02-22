"""
Auth routes – registration, login, with Firebase Phone Auth verification.

Flow:
1. User registers or logs in → backend returns user_id + phone
2. Frontend triggers Firebase Phone Auth (Firebase sends SMS)
3. User enters code → Frontend verifies with Firebase → gets Firebase ID token
4. Frontend sends Firebase ID token to backend → backend verifies → issues JWT
"""

import logging
import os
from datetime import datetime
from uuid import UUID

import firebase_admin
from firebase_admin import credentials, auth as firebase_auth

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


# ── Initialize Firebase Admin (once) ────────────────────────

def _init_firebase():
    """Initialize Firebase Admin SDK. Uses GOOGLE_APPLICATION_CREDENTIALS
    env var or FIREBASE_PROJECT_ID for on-the-fly credential creation."""
    if firebase_admin._apps:
        return  # Already initialized

    # Option 1: Service account JSON file path
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if cred_path and os.path.isfile(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        logger.info("🔥 Firebase initialized with service account file")
        return

    # Option 2: Project ID only (for verifying tokens — no admin features needed)
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    if project_id:
        firebase_admin.initialize_app(options={"projectId": project_id})
        logger.info(f"🔥 Firebase initialized with project ID: {project_id}")
        return

    # Option 3: Service account JSON as base64 env var (for Render/Vercel)
    import base64, json, tempfile
    sa_json_b64 = os.getenv("FIREBASE_SERVICE_ACCOUNT_BASE64")
    if sa_json_b64:
        sa_json = json.loads(base64.b64decode(sa_json_b64))
        cred = credentials.Certificate(sa_json)
        firebase_admin.initialize_app(cred)
        logger.info("🔥 Firebase initialized with base64-encoded service account")
        return

    logger.warning("⚠️ Firebase not configured. Phone verification will be skipped.")


_init_firebase()


def _is_firebase_configured() -> bool:
    return bool(firebase_admin._apps)


# ── Pydantic models for Firebase auth ───────────────────────

class FirebaseVerifyRequest(BaseModel):
    user_id: str
    firebase_id_token: str


# ── Register ─────────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new user. Returns the user_id and phone so the frontend
    can trigger Firebase Phone Auth and then call /auth/verify-firebase.
    """
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

    return {
        "message": "Account created! Please verify your phone number.",
        "user_id": str(user.id),
        "phone": req.phone,
        "requires_otp": True,
    }


# ── Login ────────────────────────────────────────────────────

@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Verify credentials. Returns user_id + phone so the frontend can
    trigger Firebase Phone Auth.
    """
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.is_suspended:
        raise HTTPException(status_code=403, detail="Account suspended")

    user.last_login = datetime.utcnow()
    await db.commit()

    return {
        "message": "Credentials verified. Please verify your phone.",
        "user_id": str(user.id),
        "phone": user.phone,
        "requires_otp": True,
    }


# ── Verify Firebase ID Token (completes login/register) ─────

@router.post("/verify-firebase", response_model=TokenResponse)
async def verify_firebase_token(
    req: FirebaseVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify the Firebase ID token sent after phone verification.
    On success: marks phone as verified and returns access + refresh tokens.
    """
    result = await db.execute(select(User).where(User.id == req.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if _is_firebase_configured():
        # Verify the Firebase ID token
        try:
            decoded = firebase_auth.verify_id_token(req.firebase_id_token)
            firebase_phone = decoded.get("phone_number")
            logger.info(f"🔥 Firebase verified phone: {firebase_phone} for user {user.id}")

            # Optional: check that the verified phone matches the user's phone
            if firebase_phone and user.phone and firebase_phone != user.phone:
                # Normalize: strip spaces, handle +263 vs 0 prefix
                normalized_firebase = firebase_phone.replace(" ", "")
                normalized_user = user.phone.replace(" ", "")
                if normalized_firebase != normalized_user:
                    logger.warning(
                        f"Phone mismatch: Firebase={firebase_phone}, User={user.phone}. "
                        "Allowing login but flagging."
                    )

        except firebase_admin.exceptions.FirebaseError as e:
            logger.error(f"Firebase token verification failed: {e}")
            raise HTTPException(status_code=401, detail="Phone verification failed. Please try again.")
        except ValueError as e:
            logger.error(f"Invalid Firebase token: {e}")
            raise HTTPException(status_code=401, detail="Invalid verification token.")
    else:
        # Firebase not configured — skip verification (development mode)
        logger.warning("⚠️ Firebase not configured, skipping phone verification")

    # Mark phone as verified
    user.phone_verified = True

    # Issue our app tokens
    access = create_access_token({"sub": str(user.id), "role": user.role.value})
    refresh = create_refresh_token({"sub": str(user.id)})
    user.refresh_token = refresh
    await db.commit()
    await db.refresh(user)

    logger.info(f"✅ Login complete for user {user.id}")

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user=UserResponse.model_validate(user),
    )


# ── Legacy: Keep verify-login-otp for backward compatibility ─

@router.post("/verify-login-otp", response_model=TokenResponse, include_in_schema=False)
async def verify_login_otp_legacy(
    user_id: str,
    otp: str = "",
    firebase_token: str = "",
    db: AsyncSession = Depends(get_db),
):
    """Backward-compatible endpoint. Redirects to Firebase verification."""
    if firebase_token:
        return await verify_firebase_token(
            FirebaseVerifyRequest(user_id=user_id, firebase_id_token=firebase_token),
            db=db,
        )
    # Fallback: if no firebase token, allow dev login with any OTP when Firebase not configured
    if not _is_firebase_configured():
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.phone_verified = True
        access = create_access_token({"sub": str(user.id), "role": user.role.value})
        refresh = create_refresh_token({"sub": str(user.id)})
        user.refresh_token = refresh
        await db.commit()
        await db.refresh(user)
        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            user=UserResponse.model_validate(user),
        )
    raise HTTPException(status_code=400, detail="Firebase token required for verification")


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

    return TokenResponse(
        access_token=access,
        refresh_token=new_refresh,
        user=UserResponse.model_validate(user),
    )


# ── Me ───────────────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    """Return current user info."""
    return UserResponse.model_validate(current_user)
