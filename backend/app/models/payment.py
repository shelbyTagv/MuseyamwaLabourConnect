"""
Payment model – Pesepay payment records.
"""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Enum as SAEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    ECOCASH = "ecocash"
    INNBUCKS = "innbucks"
    VISA = "visa"
    MASTERCARD = "mastercard"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount_usd = Column(Float, nullable=False)
    tokens_purchased = Column(Float, default=0)
    status = Column(SAEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    method = Column(SAEnum(PaymentMethod), nullable=True)

    # Pesepay reference
    pesepay_reference = Column(String(255), nullable=True, unique=True)
    pesepay_poll_url = Column(String(500), nullable=True)
    redirect_url = Column(String(500), nullable=True)

    description = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Payment {self.id} ({self.status})>"
