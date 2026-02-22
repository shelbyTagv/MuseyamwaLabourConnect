"""
Job model – full lifecycle from REQUESTED to RATED.
"""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Text, Float, Integer, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class JobStatus(str, enum.Enum):
    REQUESTED = "requested"
    OFFERED = "offered"
    ASSIGNED = "assigned"
    EN_ROUTE = "en_route"
    ON_SITE = "on_site"
    COMPLETED = "completed"
    RATED = "rated"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    DISPUTED = "disputed"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    status = Column(SAEnum(JobStatus), default=JobStatus.REQUESTED, nullable=False)

    # Token cost to post this job
    token_cost = Column(Integer, default=2)

    # Location where job should be performed
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_name = Column(String(255), nullable=True)

    # Budget
    budget_min = Column(Float, nullable=True)
    budget_max = Column(Float, nullable=True)
    agreed_price = Column(Float, nullable=True)

    # Participants
    employer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    worker_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    assigned_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    employer = relationship("User", foreign_keys=[employer_id])
    worker = relationship("User", foreign_keys=[worker_id])
    offers = relationship("Offer", back_populates="job", cascade="all, delete-orphan")
    ratings = relationship("Rating", back_populates="job")

    def __repr__(self):
        return f"<Job {self.title} ({self.status})>"
