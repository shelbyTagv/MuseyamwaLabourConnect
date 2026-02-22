"""
Token wallet and transaction models.
"""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class TransactionType(str, enum.Enum):
    PURCHASE = "purchase"
    DEDUCTION = "deduction"
    REFUND = "refund"
    ADMIN_GRANT = "admin_grant"
    REGISTRATION_BONUS = "registration_bonus"


class TokenWallet(Base):
    __tablename__ = "token_wallets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    balance = Column(Integer, default=0, nullable=False)
    total_purchased = Column(Integer, default=0)
    total_spent = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="token_wallet")
    transactions = relationship("TokenTransaction", back_populates="wallet", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TokenWallet user={self.user_id} balance={self.balance}>"


class TokenTransaction(Base):
    __tablename__ = "token_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("token_wallets.id", ondelete="CASCADE"), nullable=False)
    type = Column(SAEnum(TransactionType), nullable=False)
    amount = Column(Integer, nullable=False)  # positive = credit, negative = debit
    balance_after = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    reference_id = Column(String(255), nullable=True)  # payment or job id

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    wallet = relationship("TokenWallet", back_populates="transactions")

    def __repr__(self):
        return f"<TokenTransaction {self.type} amount={self.amount}>"
