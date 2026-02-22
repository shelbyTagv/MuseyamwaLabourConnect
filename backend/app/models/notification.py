"""
Notification model – in-app and push notifications.
"""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class NotificationType(str, enum.Enum):
    JOB_REQUEST = "job_request"
    JOB_OFFER = "job_offer"
    JOB_ASSIGNED = "job_assigned"
    JOB_COMPLETED = "job_completed"
    JOB_CANCELLED = "job_cancelled"
    PAYMENT = "payment"
    MESSAGE = "message"
    RATING = "rating"
    SYSTEM = "system"
    VERIFICATION = "verification"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(SAEnum(NotificationType), nullable=False)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False)
    action_url = Column(String(500), nullable=True)
    reference_id = Column(String(255), nullable=True)  # related entity id

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification {self.type} for user={self.user_id}>"
