"""
Job lifecycle service – state machine transitions and validation.
"""

from datetime import datetime
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.job import Job, JobStatus

# Valid state transitions
VALID_TRANSITIONS = {
    JobStatus.REQUESTED: [JobStatus.OFFERED, JobStatus.CANCELLED],
    JobStatus.OFFERED: [JobStatus.ASSIGNED, JobStatus.CANCELLED, JobStatus.REQUESTED],
    JobStatus.ASSIGNED: [JobStatus.EN_ROUTE, JobStatus.CANCELLED, JobStatus.NO_SHOW],
    JobStatus.EN_ROUTE: [JobStatus.ON_SITE, JobStatus.CANCELLED, JobStatus.NO_SHOW],
    JobStatus.ON_SITE: [JobStatus.COMPLETED, JobStatus.DISPUTED],
    JobStatus.COMPLETED: [JobStatus.RATED, JobStatus.DISPUTED],
    JobStatus.RATED: [],
    JobStatus.CANCELLED: [],
    JobStatus.NO_SHOW: [JobStatus.DISPUTED],
    JobStatus.DISPUTED: [JobStatus.COMPLETED, JobStatus.CANCELLED],
}


async def transition_job(
    db: AsyncSession,
    job: Job,
    new_status: JobStatus,
    worker_id: UUID = None,
) -> Job:
    """Transition a job to a new status with validation."""
    allowed = VALID_TRANSITIONS.get(job.status, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from {job.status} to {new_status}. Allowed: {allowed}",
        )

    job.status = new_status

    if new_status == JobStatus.ASSIGNED and worker_id:
        job.worker_id = worker_id
        job.assigned_at = datetime.utcnow()

    if new_status == JobStatus.COMPLETED:
        job.completed_at = datetime.utcnow()

    job.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(job)
    return job


async def get_nearby_jobs(
    db: AsyncSession,
    latitude: float,
    longitude: float,
    radius_km: float = 50,
    limit: int = 50,
):
    """
    Find open jobs near a location using approximate distance.
    Uses the equirectangular approximation for speed.
    """
    # ~111 km per degree latitude
    lat_range = radius_km / 111.0
    lng_range = radius_km / (111.0 * abs(max(0.01, __import__("math").cos(__import__("math").radians(latitude)))))

    result = await db.execute(
        select(Job)
        .where(
            Job.status == JobStatus.REQUESTED,
            Job.latitude.isnot(None),
            Job.latitude.between(latitude - lat_range, latitude + lat_range),
            Job.longitude.between(longitude - lng_range, longitude + lng_range),
        )
        .order_by(Job.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
