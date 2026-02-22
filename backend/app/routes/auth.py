"""
Auth routes – registration, login (with OTP verification), token refresh.
On every login or first-time register, a 6-digit OTP is sent to the user's
phone. They must enter it before receiving access tokens.
"""

import random
import logging
from datetime import datetime, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.token import TokenWallet
from app.schemas import (
    RegisterRequest, LoginRequest, TokenResponse, RefreshRequest, UserResponse,
    SendOTPRequest, VerifyOTPRequest, OTPResponse,
)
from app.services.auth import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    decode_token, get_current_user,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Helper: generate & store OTP ────────────────────────────

async def _generate_and_send_otp(user: User, db: AsyncSession) -> str:
    """Generate a 6-digit OTP, store on user, and log it (plug in SMS later)."""
    otp = f"{random.randint(100000, 999999)}"
    user.phone_otp = otp
    user.phone_otp_expires = datetime.utcnow() + timedelta(minutes=10)
    await db.commit()

    # TODO: Replace with real SMS (Twilio / Africa's Talking)
    logger.info(f"📱 OTP for {user.phone}: {otp}")
    print(f"📱 OTP for {user.phone}: {otp}")  # Visible in Render logs
    return otp


# ── Register ─────────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new user. Returns the user_id and sends an OTP to their phone.
    They must call /auth/verify-login-otp to get access tokens.
    """
    # Check existing
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

    # Create profile
    profile = Profile(user_id=user.id)
    db.add(profile)

    # Create token wallet
    wallet = TokenWallet(user_id=user.id, balance=0)
    db.add(wallet)

    await db.commit()
    await db.refresh(user)

    # Send OTP for phone verification
    await _generate_and_send_otp(user, db)

    return {
        "message": f"Account created! A verification code has been sent to {req.phone}.",
        "user_id": str(user.id),
        "phone": req.phone,
        "requires_otp": True,
    }


# ── Login ────────────────────────────────────────────────────

@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Verify credentials and send OTP to user's phone.
    Does NOT return tokens yet — user must verify OTP first.
    """
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.is_suspended:
        raise HTTPException(status_code=403, detail="Account suspended")

    user.last_login = datetime.utcnow()
    await db.commit()

    # Send OTP
    await _generate_and_send_otp(user, db)

    return {
        "message": f"Verification code sent to {user.phone}.",
        "user_id": str(user.id),
        "phone": user.phone,
        "requires_otp": True,
    }


# ── Verify Login OTP (completes login/register) ─────────────

@router.post("/verify-login-otp", response_model=TokenResponse)
async def verify_login_otp(
    user_id: str,
    otp: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify the 6-digit OTP sent after login/register.
    On success: marks phone as verified and returns access + refresh tokens.
    """
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

    # Mark phone as verified + clear OTP
    user.phone_verified = True
    user.phone_otp = None
    user.phone_otp_expires = None

    # Issue tokens
    access = create_access_token({"sub": str(user.id), "role": user.role.value})
    refresh = create_refresh_token({"sub": str(user.id)})
    user.refresh_token = refresh
    await db.commit()
    await db.refresh(user)

    logger.info(f"✅ OTP verified, login complete for user {user.id}")

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user=UserResponse.model_validate(user),
    )


# ── Resend OTP ───────────────────────────────────────────────

@router.post("/resend-otp")
async def resend_otp(user_id: str, db: AsyncSession = Depends(get_db)):
    """Resend a fresh OTP to the user's phone."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await _generate_and_send_otp(user, db)

    return {
        "message": f"New verification code sent to {user.phone}.",
        "phone": user.phone,
    }


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
