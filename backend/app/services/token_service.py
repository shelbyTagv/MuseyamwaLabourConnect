"""
Token economy service – balance management, deductions, top-ups.
"""

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.token import TokenWallet, TokenTransaction, TransactionType


async def get_or_create_wallet(db: AsyncSession, user_id: UUID) -> TokenWallet:
    """Get user's wallet, creating one if it doesn't exist."""
    result = await db.execute(select(TokenWallet).where(TokenWallet.user_id == user_id))
    wallet = result.scalar_one_or_none()
    if not wallet:
        wallet = TokenWallet(user_id=user_id, balance=0)
        db.add(wallet)
        await db.commit()
        await db.refresh(wallet)
    return wallet


async def credit_tokens(
    db: AsyncSession,
    user_id: UUID,
    amount: int,
    tx_type: TransactionType,
    description: str = "",
    reference_id: str = None,
) -> TokenWallet:
    """Add tokens to wallet and record transaction."""
    wallet = await get_or_create_wallet(db, user_id)
    wallet.balance += amount
    wallet.total_purchased += amount

    tx = TokenTransaction(
        wallet_id=wallet.id,
        type=tx_type,
        amount=amount,
        balance_after=wallet.balance,
        description=description,
        reference_id=reference_id,
    )
    db.add(tx)
    await db.commit()
    await db.refresh(wallet)
    return wallet


async def deduct_tokens(
    db: AsyncSession,
    user_id: UUID,
    amount: int,
    description: str = "",
    reference_id: str = None,
) -> TokenWallet:
    """Deduct tokens; raises 402 if insufficient balance."""
    wallet = await get_or_create_wallet(db, user_id)
    if wallet.balance < amount:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient tokens. Balance: {wallet.balance}, required: {amount}",
        )
    wallet.balance -= amount
    wallet.total_spent += amount

    tx = TokenTransaction(
        wallet_id=wallet.id,
        type=TransactionType.DEDUCTION,
        amount=-amount,
        balance_after=wallet.balance,
        description=description,
        reference_id=reference_id,
    )
    db.add(tx)
    await db.commit()
    await db.refresh(wallet)
    return wallet


async def get_transactions(db: AsyncSession, user_id: UUID, limit: int = 50):
    """Return recent token transactions."""
    wallet = await get_or_create_wallet(db, user_id)
    result = await db.execute(
        select(TokenTransaction)
        .where(TokenTransaction.wallet_id == wallet.id)
        .order_by(TokenTransaction.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
