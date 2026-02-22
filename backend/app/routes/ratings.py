"""
Rating routes.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.job import Job, JobStatus
from app.models.rating import Rating
from app.models.profile import Profile
from app.schemas import RatingCreateRequest, RatingResponse
from app.services.auth import get_current_user
from app.services.notification_service import create_notification
from app.models.notification import NotificationType

router = APIRouter(prefix="/ratings", tags=["Ratings"])


@router.post("/", response_model=RatingResponse, status_code=201)
async def submit_rating(
    req: RatingCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a rating after job completion."""
    # Verify job is completed/rated
    result = await db.execute(select(Job).where(Job.id == req.job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in (JobStatus.COMPLETED, JobStatus.RATED):
        raise HTTPException(status_code=400, detail="Job must be completed first")

    # Verify user is participant
    if current_user.id not in (job.employer_id, job.worker_id):
        raise HTTPException(status_code=403, detail="Not a participant")

    # Check duplicate
    existing = await db.execute(
        select(Rating).where(Rating.job_id == req.job_id, Rating.rater_id == current_user.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already rated this job")

    rating = Rating(
        job_id=req.job_id,
        rater_id=current_user.id,
        rated_id=req.rated_id,
        stars=req.stars,
        comment=req.comment,
        tags=req.tags,
    )
    db.add(rating)
    await db.commit()

    # Update profile average
    avg_result = await db.execute(
        select(func.avg(Rating.stars), func.count(Rating.id))
        .where(Rating.rated_id == req.rated_id)
    )
    row = avg_result.one()
    profile_result = await db.execute(select(Profile).where(Profile.user_id == req.rated_id))
    profile = profile_result.scalar_one_or_none()
    if profile:
        profile.average_rating = round(float(row[0] or 0), 2)
        profile.total_ratings = row[1] or 0
        await db.commit()

    # Update job status to RATED if both parties rated
    all_ratings = await db.execute(
        select(func.count(Rating.id)).where(Rating.job_id == req.job_id)
    )
    if all_ratings.scalar() >= 2:
        job.status = JobStatus.RATED
        await db.commit()

    await create_notification(
        db, req.rated_id, NotificationType.RATING,
        title=f"New {req.stars}★ rating",
        body=req.comment or "You received a new rating",
        reference_id=str(rating.id),
    )

    await db.refresh(rating)
    return RatingResponse.model_validate(rating)


@router.get("/user/{user_id}", response_model=list[RatingResponse])
async def get_user_ratings(
    user_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get all ratings received by a user."""
    result = await db.execute(
        select(Rating)
        .where(Rating.rated_id == user_id)
        .order_by(Rating.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return [RatingResponse.model_validate(r) for r in result.scalars().all()]
