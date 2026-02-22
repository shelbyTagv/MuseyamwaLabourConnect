"""
Profile model – extended user details, skills, and profession tags.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.database import Base


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    profession_tags = Column(ARRAY(String), default=list)
    skills = Column(ARRAY(String), default=list)
    experience_years = Column(Float, default=0)
    hourly_rate = Column(Float, nullable=True)
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    id_document_url = Column(String(500), nullable=True)  # encrypted path

    # Computed ratings cache
    average_rating = Column(Float, default=0.0)
    total_ratings = Column(Float, default=0)
    total_jobs_completed = Column(Float, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="profile")

    def __repr__(self):
        return f"<Profile user_id={self.user_id}>"
