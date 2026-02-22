"""
Auth routes – registration, login, token refresh.
"""

from fastapi import APIRouter, Depends, HTTPException, status
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

    from datetime import datetime
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
