"""
Rating model – star ratings with tags for job completion.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.database import Base


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    rater_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    rated_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    stars = Column(Float, nullable=False)  # 1.0 – 5.0
    comment = Column(Text, nullable=True)
    tags = Column(ARRAY(String), default=list)  # e.g. ["punctual", "professional", "skilled"]

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job = relationship("Job", back_populates="ratings")
    rater = relationship("User", foreign_keys=[rater_id], back_populates="ratings_given")
    rated = relationship("User", foreign_keys=[rated_id], back_populates="ratings_received")

    def __repr__(self):
        return f"<Rating {self.stars}★ for user={self.rated_id}>"
