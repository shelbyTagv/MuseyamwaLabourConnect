"""
Admin dashboard routes – user management, analytics, audit logs.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.profile import Profile
from app.models.job import Job, JobStatus
from app.models.token import TokenWallet, TokenTransaction, TransactionType
from app.models.payment import Payment, PaymentStatus
from app.models.audit_log import AuditLog
from app.schemas import (
    UserResponse, AdminUserUpdateRequest, DashboardStats,
    AuditLogResponse,
)
from app.services.auth import get_current_user, require_role

router = APIRouter(prefix="/admin", tags=["Admin"])


async def log_action(db: AsyncSession, user_id: UUID, action: str, entity_type: str = None,
                     entity_id: str = None, details: dict = None, ip: str = None):
    """Create an audit log entry."""
    entry = AuditLog(
        user_id=user_id, action=action,
        entity_type=entity_type, entity_id=entity_id,
        details=details, ip_address=ip,
    )
    db.add(entry)
    await db.commit()


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard_stats(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Get platform analytics."""
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    total_employers = (await db.execute(
        select(func.count(User.id)).where(User.role == UserRole.EMPLOYER)
    )).scalar() or 0
    total_employees = (await db.execute(
        select(func.count(User.id)).where(User.role == UserRole.EMPLOYEE)
    )).scalar() or 0
    total_jobs = (await db.execute(select(func.count(Job.id)))).scalar() or 0
    active_jobs = (await db.execute(
        select(func.count(Job.id)).where(Job.status.in_([
            JobStatus.REQUESTED, JobStatus.OFFERED, JobStatus.ASSIGNED,
            JobStatus.EN_ROUTE, JobStatus.ON_SITE,
        ]))
    )).scalar() or 0
    completed_jobs = (await db.execute(
        select(func.count(Job.id)).where(Job.status.in_([JobStatus.COMPLETED, JobStatus.RATED]))
    )).scalar() or 0
    total_tokens = (await db.execute(
        select(func.coalesce(func.sum(TokenTransaction.amount), 0))
        .where(TokenTransaction.type == TransactionType.PURCHASE)
    )).scalar() or 0
    total_revenue = (await db.execute(
        select(func.coalesce(func.sum(Payment.amount_usd), 0))
        .where(Payment.status == PaymentStatus.COMPLETED)
    )).scalar() or 0
    online_workers = (await db.execute(
        select(func.count(User.id)).where(User.is_online == True, User.role == UserRole.EMPLOYEE)
    )).scalar() or 0

    return DashboardStats(
        total_users=total_users,
        total_employers=total_employers,
        total_employees=total_employees,
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        completed_jobs=completed_jobs,
        total_tokens_sold=total_tokens,
        total_revenue_usd=float(total_revenue),
        online_workers=online_workers,
    )


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    role: UserRole = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """List all users with optional role filter."""
    query = select(User)
    if role:
        query = query.where(User.role == role)
    query = query.order_by(User.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    return [UserResponse.model_validate(u) for u in result.scalars().all()]


@router.patch("/users/{user_id}", response_model=UserResponse)
async def admin_update_user(
    user_id: UUID,
    req: AdminUserUpdateRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Admin: verify, suspend, or update a user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    changes = {}
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
        changes[field] = str(value)

    await db.commit()
    await db.refresh(user)

    await log_action(db, current_user.id, "admin_update_user",
                     entity_type="user", entity_id=str(user_id), details=changes)

    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}")
async def admin_delete_user(
    user_id: UUID,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Admin: delete a user account."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()
    await log_action(db, current_user.id, "admin_delete_user",
                     entity_type="user", entity_id=str(user_id))
    return {"status": "deleted"}


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def list_audit_logs(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """List audit logs."""
    result = await db.execute(
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return [AuditLogResponse.model_validate(a) for a in result.scalars().all()]


@router.post("/tokens/grant")
async def grant_tokens(
    user_id: UUID = Query(...),
    amount: int = Query(..., gt=0),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Admin: grant tokens to a user."""
    from app.services.token_service import credit_tokens
    wallet = await credit_tokens(
        db, user_id, amount,
        tx_type=TransactionType.ADMIN_GRANT,
        description=f"Admin grant by {current_user.email}",
    )
    await log_action(db, current_user.id, "admin_grant_tokens",
                     entity_type="user", entity_id=str(user_id),
                     details={"amount": amount})
    return {"status": "ok", "new_balance": wallet.balance}
