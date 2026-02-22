"""
Payment routes – Pesepay webhook and payment status.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.payment import Payment, PaymentStatus
from app.models.token import TransactionType
from app.schemas import PaymentResponse
from app.services.auth import get_current_user
from app.services.token_service import credit_tokens
from app.services.pesepay import pesepay_client
from app.services.notification_service import create_notification
from app.models.notification import NotificationType
from app.models.user import User

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/webhook")
async def pesepay_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Pesepay payment result callback."""
    body = await request.json()

    reference = body.get("referenceNumber") or body.get("merchantReference")
    if not reference:
        raise HTTPException(status_code=400, detail="Missing reference")

    result = await db.execute(
        select(Payment).where(
            (Payment.pesepay_reference == reference) | (Payment.id == reference)
        )
    )
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    tx_status = body.get("transactionStatus", "").upper()
    if tx_status == "SUCCESS":
        payment.status = PaymentStatus.COMPLETED
        # Credit tokens
        await credit_tokens(
            db, payment.user_id,
            int(payment.tokens_purchased),
            tx_type=TransactionType.PURCHASE,
            description=f"Purchased {int(payment.tokens_purchased)} tokens",
            reference_id=str(payment.id),
        )
        await create_notification(
            db, payment.user_id, NotificationType.PAYMENT,
            title="Tokens purchased!",
            body=f"{int(payment.tokens_purchased)} tokens added to your wallet.",
        )
    elif tx_status == "FAILED":
        payment.status = PaymentStatus.FAILED
    else:
        payment.status = PaymentStatus.PENDING

    await db.commit()
    return {"status": "ok"}


@router.get("/{payment_id}/status", response_model=PaymentResponse)
async def check_payment(
    payment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Poll payment status."""
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # If still pending, poll Pesepay
    if payment.status == PaymentStatus.PENDING and payment.pesepay_poll_url:
        try:
            poll_result = await pesepay_client.check_payment_status(payment.pesepay_poll_url)
            if poll_result.get("transactionStatus") == "SUCCESS":
                payment.status = PaymentStatus.COMPLETED
                await credit_tokens(
                    db, payment.user_id,
                    int(payment.tokens_purchased),
                    tx_type=TransactionType.PURCHASE,
                    description=f"Purchased {int(payment.tokens_purchased)} tokens",
                    reference_id=str(payment.id),
                )
            elif poll_result.get("transactionStatus") == "FAILED":
                payment.status = PaymentStatus.FAILED
            await db.commit()
        except Exception:
            pass

    return PaymentResponse.model_validate(payment)
