"""
Token wallet and purchase routes.
Handles seamless Pesepay flow with automatic verification polling.
"""

import asyncio
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, AsyncSessionLocal
from app.models.user import User
from app.schemas import (
    WalletResponse, TransactionResponse, TokenPurchaseRequest, PaymentResponse,
)
from app.services.auth import get_current_user
from app.services.token_service import get_or_create_wallet, credit_tokens, get_transactions
from app.services.pesepay import pesepay_client
from app.models.token import TransactionType
from app.models.payment import Payment, PaymentStatus
from app.services.notification_service import create_notification
from app.models.notification import NotificationType
from app.config import settings
from sqlalchemy import select

logger = logging.getLogger(__name__)

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


async def _poll_and_complete_payment(payment_id: UUID, reference: str):
    """
    Background task: Poll Pesepay until the payment completes or fails,
    then credit tokens automatically.
    """
    try:
        result = await pesepay_client.poll_until_complete(reference, max_attempts=24, interval=5.0)
        status = result["status"]

        async with AsyncSessionLocal() as db:
            res = await db.execute(select(Payment).where(Payment.id == payment_id))
            payment = res.scalar_one_or_none()
            if not payment or payment.status != PaymentStatus.PENDING:
                return

            if status == "SUCCESS":
                payment.status = PaymentStatus.COMPLETED
                # Credit tokens to the user
                await credit_tokens(
                    db, payment.user_id,
                    int(payment.tokens_purchased),
                    tx_type=TransactionType.PURCHASE,
                    description=f"Purchased {int(payment.tokens_purchased)} tokens via {payment.method}",
                    reference_id=str(payment.id),
                )
                await create_notification(
                    db, payment.user_id, NotificationType.PAYMENT,
                    title="🎉 Payment successful!",
                    body=f"{int(payment.tokens_purchased)} tokens have been added to your wallet.",
                )
                logger.info(f"Payment {payment_id} completed. {payment.tokens_purchased} tokens credited.")
            elif status == "FAILED":
                payment.status = PaymentStatus.FAILED
                await create_notification(
                    db, payment.user_id, NotificationType.PAYMENT,
                    title="❌ Payment failed",
                    body="Your token purchase could not be completed. Please try again.",
                )
                logger.info(f"Payment {payment_id} failed.")
            else:
                # Still pending after max attempts
                logger.warning(f"Payment {payment_id} still pending after max polling attempts.")

            await db.commit()
    except Exception as e:
        logger.error(f"Background payment polling error: {e}")


@router.post("/purchase", response_model=PaymentResponse)
async def purchase_tokens(
    req: TokenPurchaseRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Initiate a seamless token purchase via Pesepay.
    1. Creates a payment record
    2. Sends seamless payment to Pesepay (USSD push to user's phone)
    3. Starts background polling for automatic verification
    4. Returns payment info for frontend status tracking
    """
    phone = req.phone or current_user.phone
    if not phone:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Phone number required for mobile payment")

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

    # Initiate seamless Pesepay payment (triggers USSD push to phone)
    result = await pesepay_client.make_seamless_payment(
        amount=total_usd,
        reason=f"MuseyamwaLabourConnect: {req.amount} tokens",
        method=req.method.value,
        phone=phone,
        reference=str(payment.id),
    )

    payment.pesepay_reference = result["reference"]
    payment.pesepay_poll_url = result.get("poll_url", "")
    payment.redirect_url = result.get("redirect_url", "")
    await db.commit()
    await db.refresh(payment)

    # Start background polling for auto-verification
    background_tasks.add_task(
        _poll_and_complete_payment,
        payment.id,
        result["reference"],
    )

    logger.info(f"Payment {payment.id} initiated for user {current_user.id}: {req.amount} tokens, ${total_usd}")

    return PaymentResponse.model_validate(payment)


@router.get("/purchase/{payment_id}/status", response_model=PaymentResponse)
async def check_purchase_status(
    payment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Check the current status of a token purchase.
    Frontend polls this endpoint to update the UI in real-time.
    """
    result = await db.execute(
        select(Payment).where(Payment.id == payment_id, Payment.user_id == current_user.id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Payment not found")

    # If still pending, try a live check against Pesepay
    if payment.status == PaymentStatus.PENDING and payment.pesepay_reference:
        try:
            status_data = await pesepay_client.check_payment_status(payment.pesepay_reference)
            tx_status = status_data.get("transactionStatus", "").upper()

            if tx_status in ("SUCCESS", "PAID"):
                payment.status = PaymentStatus.COMPLETED
                await credit_tokens(
                    db, payment.user_id,
                    int(payment.tokens_purchased),
                    tx_type=TransactionType.PURCHASE,
                    description=f"Purchased {int(payment.tokens_purchased)} tokens",
                    reference_id=str(payment.id),
                )
                await db.commit()
            elif tx_status in ("FAILED", "CANCELLED", "DECLINED"):
                payment.status = PaymentStatus.FAILED
                await db.commit()
        except Exception:
            pass  # Background poller will catch it

    return PaymentResponse.model_validate(payment)
