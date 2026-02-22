"""
Auth routes – registration, login, token refresh, phone verification.
"""

import random
import logging
from datetime import datetime, timedelta
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


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user (employer or employee)."""
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

    access = create_access_token({"sub": str(user.id), "role": user.role.value})
    refresh = create_refresh_token({"sub": str(user.id)})
    user.refresh_token = refresh
    await db.commit()

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate and return tokens."""
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.is_suspended:
        raise HTTPException(status_code=403, detail="Account suspended")

    user.last_login = datetime.utcnow()

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


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    """Return current user info."""
    return UserResponse.model_validate(current_user)


# ── Phone Verification (OTP) ──────────────────────────────────


@router.post("/send-otp", response_model=OTPResponse)
async def send_otp(
    req: SendOTPRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a 6-digit OTP and send it to the user's phone.
    For now, the OTP is logged (plug in an SMS provider like Twilio or Africa's Talking).
    """
    if current_user.phone_verified:
        return OTPResponse(message="Phone already verified", phone_verified=True)

    # Generate 6-digit OTP
    otp = f"{random.randint(100000, 999999)}"
    current_user.phone_otp = otp
    current_user.phone_otp_expires = datetime.utcnow() + timedelta(minutes=10)
    await db.commit()

    # TODO: Send OTP via SMS. For now, log it.
    phone = req.phone or current_user.phone
    logger.info(f"📱 OTP for {phone}: {otp}")
    print(f"📱 OTP for {phone}: {otp}")  # Visible in Render logs

    return OTPResponse(
        message=f"Verification code sent to {phone}. Check your phone.",
        phone_verified=False,
    )


@router.post("/verify-otp", response_model=OTPResponse)
async def verify_otp(
    req: VerifyOTPRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify the OTP and mark the phone as verified."""
    if current_user.phone_verified:
        return OTPResponse(message="Phone already verified", phone_verified=True)

    if not current_user.phone_otp:
        raise HTTPException(status_code=400, detail="No OTP sent. Request one first.")

    if current_user.phone_otp_expires and datetime.utcnow() > current_user.phone_otp_expires:
        current_user.phone_otp = None
        current_user.phone_otp_expires = None
        await db.commit()
        raise HTTPException(status_code=400, detail="OTP expired. Request a new one.")

    if req.otp != current_user.phone_otp:
        raise HTTPException(status_code=400, detail="Invalid OTP code")

    # Mark phone as verified
    current_user.phone_verified = True
    current_user.phone_otp = None
    current_user.phone_otp_expires = None
    await db.commit()

    logger.info(f"✅ Phone verified for user {current_user.id}")

    return OTPResponse(message="Phone verified successfully!", phone_verified=True)

