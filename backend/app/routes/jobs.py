"""
Job lifecycle routes.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.job import Job, JobStatus
from app.schemas import JobCreateRequest, JobResponse, JobStatusUpdateRequest
from app.services.auth import get_current_user, require_role
from app.services.token_service import deduct_tokens
from app.services.job_service import transition_job, get_nearby_jobs
from app.services.notification_service import create_notification
from app.models.notification import NotificationType
from app.config import settings

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("/", response_model=JobResponse, status_code=201)
async def create_job(
    req: JobCreateRequest,
    current_user: User = Depends(require_role(UserRole.EMPLOYER)),
    db: AsyncSession = Depends(get_db),
):
    """Post a job (consumes tokens)."""
    # Deduct tokens
    await deduct_tokens(
        db, current_user.id, settings.JOB_POST_TOKEN_COST,
        description=f"Job posting: {req.title}",
    )

    job = Job(
        title=req.title,
        description=req.description,
        category=req.category,
        latitude=req.latitude,
        longitude=req.longitude,
        location_name=req.location_name,
        budget_min=req.budget_min,
        budget_max=req.budget_max,
        token_cost=settings.JOB_POST_TOKEN_COST,
        employer_id=current_user.id,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return JobResponse.model_validate(job)


@router.get("/", response_model=list[JobResponse])
async def list_jobs(
    status_filter: JobStatus = Query(None, alias="status"),
    category: str = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List jobs with optional filters."""
    query = select(Job)
    if status_filter:
        query = query.where(Job.status == status_filter)
    if category:
        query = query.where(Job.category == category)

    # Employers see their own jobs; employees see open jobs
    if current_user.role == UserRole.EMPLOYER:
        query = query.where(Job.employer_id == current_user.id)
    elif current_user.role == UserRole.EMPLOYEE:
        query = query.where(
            (Job.status == JobStatus.REQUESTED) | (Job.worker_id == current_user.id)
        )

    query = query.order_by(Job.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    return [JobResponse.model_validate(j) for j in result.scalars().all()]


@router.get("/nearby", response_model=list[JobResponse])
async def nearby_jobs(
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius: float = Query(50.0),
    current_user: User = Depends(require_role(UserRole.EMPLOYEE)),
    db: AsyncSession = Depends(get_db),
):
    """Find open jobs near the employee's location."""
    jobs = await get_nearby_jobs(db, latitude, longitude, radius)
    return [JobResponse.model_validate(j) for j in jobs]


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse.model_validate(job)


@router.patch("/{job_id}/status", response_model=JobResponse)
async def update_job_status(
    job_id: UUID,
    req: JobStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Transition job to a new status."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Permission check
    if current_user.role == UserRole.EMPLOYER and job.employer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your job")
    if current_user.role == UserRole.EMPLOYEE and job.worker_id != current_user.id:
        if req.status not in (JobStatus.ASSIGNED,):  # workers can accept assignment
            raise HTTPException(status_code=403, detail="Not assigned to this job")

    job = await transition_job(db, job, req.status, worker_id=current_user.id)

    # Notify relevant party
    notify_user_id = job.worker_id if current_user.id == job.employer_id else job.employer_id
    if notify_user_id:
        await create_notification(
            db, notify_user_id, NotificationType.JOB_ASSIGNED,
            title=f"Job update: {job.title}",
            body=f"Status changed to {job.status.value}",
            reference_id=str(job.id),
        )

    return JobResponse.model_validate(job)
