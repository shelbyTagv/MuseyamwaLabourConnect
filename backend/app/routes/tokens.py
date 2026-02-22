"""
Token wallet and purchase routes.
"""

from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas import (
    WalletResponse, TransactionResponse, TokenPurchaseRequest, PaymentResponse,
)
from app.services.auth import get_current_user
from app.services.token_service import get_or_create_wallet, credit_tokens, get_transactions
from app.services.pesepay import pesepay_client
from app.models.token import TransactionType
from app.models.payment import Payment, PaymentStatus
from app.config import settings

router = APIRouter(prefix="/tokens", tags=["Tokens"])


@router.get("/wallet", response_model=WalletResponse)
async def get_wallet(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current token wallet balance."""
    wallet = await get_or_create_wallet(db, current_user.id)
    return WalletResponse.model_validate(wallet)


@router.get("/transactions", response_model=list[TransactionResponse])
async def list_transactions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List token transaction history."""
    txs = await get_transactions(db, current_user.id)
    return [TransactionResponse.model_validate(t) for t in txs]


@router.post("/purchase", response_model=PaymentResponse)
async def purchase_tokens(
    req: TokenPurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Initiate token purchase via Pesepay."""
    total_usd = req.amount * settings.DEFAULT_TOKEN_PRICE_USD

    # Create payment record
    payment = Payment(
        user_id=current_user.id,
        amount_usd=total_usd,
        tokens_purchased=req.amount,
        method=req.method,
        description=f"Purchase {req.amount} tokens",
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    # Initiate Pesepay payment
    result = await pesepay_client.initiate_payment(
        amount=total_usd,
        reason=f"MuseyamwaLabourConnect: {req.amount} tokens",
        method=req.method.value,
        phone=req.phone or current_user.phone,
        reference=str(payment.id),
    )

    payment.pesepay_reference = result["reference"]
    payment.pesepay_poll_url = result["poll_url"]
    payment.redirect_url = result.get("redirect_url", "")
    await db.commit()
    await db.refresh(payment)

    return PaymentResponse.model_validate(payment)
