"""
Offer/negotiation routes.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.job import Job, JobStatus
from app.models.offer import Offer, OfferStatus
from app.schemas import OfferCreateRequest, OfferResponse, OfferRespondRequest
from app.services.auth import get_current_user
from app.services.job_service import transition_job
from app.services.notification_service import create_notification
from app.models.notification import NotificationType
from app.services.token_service import deduct_tokens
from app.config import settings

router = APIRouter(prefix="/offers", tags=["Offers"])


@router.post("/", response_model=OfferResponse, status_code=201)
async def create_offer(
    req: OfferCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send an offer or counter-offer on a job (costs tokens)."""
    result = await db.execute(select(Job).where(Job.id == req.job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Deduct tokens for sending an offer
    await deduct_tokens(
        db, current_user.id, settings.OFFER_TOKEN_COST,
        description=f"Offer on job: {job.title}",
    )

    offer = Offer(
        job_id=req.job_id,
        from_user_id=current_user.id,
        to_user_id=req.to_user_id,
        amount=req.amount,
        message=req.message,
    )
    db.add(offer)
    await db.commit()
    await db.refresh(offer)

    # Notify recipient
    await create_notification(
        db, req.to_user_id, NotificationType.JOB_OFFER,
        title=f"New offer on: {job.title}",
        body=f"${req.amount} from {current_user.full_name}",
        reference_id=str(offer.id),
    )

    return OfferResponse.model_validate(offer)


@router.get("/job/{job_id}", response_model=list[OfferResponse])
async def list_offers(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all offers on a job."""
    result = await db.execute(
        select(Offer).where(Offer.job_id == job_id).order_by(Offer.created_at.desc())
    )
    return [OfferResponse.model_validate(o) for o in result.scalars().all()]


@router.patch("/{offer_id}", response_model=OfferResponse)
async def respond_to_offer(
    offer_id: UUID,
    req: OfferRespondRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Accept, reject, or counter an offer."""
    result = await db.execute(select(Offer).where(Offer.id == offer_id))
    offer = result.scalar_one_or_none()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    if offer.to_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    offer.status = req.status

    if req.status == OfferStatus.ACCEPTED:
        # Assign worker to job
        job_result = await db.execute(select(Job).where(Job.id == offer.job_id))
        job = job_result.scalar_one_or_none()
        if job:
            job.agreed_price = offer.amount
            await transition_job(db, job, JobStatus.ASSIGNED, worker_id=offer.to_user_id)

    elif req.status == OfferStatus.COUNTER and req.counter_amount:
        # Create counter-offer
        counter = Offer(
            job_id=offer.job_id,
            from_user_id=current_user.id,
            to_user_id=offer.from_user_id,
            amount=req.counter_amount,
            message=req.counter_message,
        )
        db.add(counter)

    await db.commit()
    await db.refresh(offer)
    return OfferResponse.model_validate(offer)
