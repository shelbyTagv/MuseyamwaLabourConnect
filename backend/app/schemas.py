"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models.user import UserRole, AdminRole
from app.models.job import JobStatus
from app.models.offer import OfferStatus
from app.models.token import TransactionType
from app.models.payment import PaymentStatus, PaymentMethod
from app.models.notification import NotificationType


# ── Auth Schemas ──────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=255)
    role: UserRole = UserRole.EMPLOYEE


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class RefreshRequest(BaseModel):
    refresh_token: str


# ── User Schemas ──────────────────────────────────────────────

class UserResponse(BaseModel):
    id: UUID
    email: str
    phone: str
    full_name: str
    role: UserRole
    admin_role: Optional[AdminRole] = None
    is_verified: bool
    is_active: bool
    is_online: bool
    phone_verified: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    is_online: Optional[bool] = None


class AdminUserUpdateRequest(BaseModel):
    is_verified: Optional[bool] = None
    is_active: Optional[bool] = None
    is_suspended: Optional[bool] = None
    admin_role: Optional[AdminRole] = None


# ── Profile Schemas ───────────────────────────────────────────

class ProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    profession_tags: List[str] = []
    skills: List[str] = []
    experience_years: float = 0
    hourly_rate: Optional[float] = None
    city: Optional[str] = None
    average_rating: float = 0.0
    total_ratings: float = 0
    total_jobs_completed: float = 0

    class Config:
        from_attributes = True


class ProfileUpdateRequest(BaseModel):
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    profession_tags: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    experience_years: Optional[float] = None
    hourly_rate: Optional[float] = None
    city: Optional[str] = None


# ── Job Schemas ───────────────────────────────────────────────

class JobCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    category: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None


class JobResponse(BaseModel):
    id: UUID
    title: str
    description: str
    category: str
    status: JobStatus
    token_cost: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    agreed_price: Optional[float] = None
    employer_id: UUID
    worker_id: Optional[UUID] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobStatusUpdateRequest(BaseModel):
    status: JobStatus


# ── Offer Schemas ─────────────────────────────────────────────

class OfferCreateRequest(BaseModel):
    job_id: UUID
    to_user_id: UUID
    amount: float
    message: Optional[str] = None


class OfferResponse(BaseModel):
    id: UUID
    job_id: UUID
    from_user_id: UUID
    to_user_id: UUID
    amount: float
    message: Optional[str] = None
    status: OfferStatus
    created_at: datetime

    class Config:
        from_attributes = True


class OfferRespondRequest(BaseModel):
    status: OfferStatus
    counter_amount: Optional[float] = None
    counter_message: Optional[str] = None


# ── Token Schemas ─────────────────────────────────────────────

class WalletResponse(BaseModel):
    id: UUID
    user_id: UUID
    balance: int
    total_purchased: int
    total_spent: int

    class Config:
        from_attributes = True


class TransactionResponse(BaseModel):
    id: UUID
    wallet_id: UUID
    type: TransactionType
    amount: int
    balance_after: int
    description: Optional[str] = None
    reference_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TokenPurchaseRequest(BaseModel):
    amount: int = Field(..., gt=0)
    method: PaymentMethod = PaymentMethod.ECOCASH
    phone: Optional[str] = None


class SendOTPRequest(BaseModel):
    phone: Optional[str] = None  # If not provided, uses user's registered phone


class VerifyOTPRequest(BaseModel):
    otp: str = Field(..., min_length=6, max_length=6)


class OTPResponse(BaseModel):
    message: str
    phone_verified: bool = False


# ── Payment Schemas ───────────────────────────────────────────

class PaymentResponse(BaseModel):
    id: UUID
    user_id: UUID
    amount_usd: float
    tokens_purchased: float
    status: PaymentStatus
    method: Optional[PaymentMethod] = None
    pesepay_reference: Optional[str] = None
    redirect_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Location Schemas ──────────────────────────────────────────

class LocationUpdateRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    accuracy: Optional[float] = None


class LocationResponse(BaseModel):
    user_id: UUID
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WorkerMapResponse(BaseModel):
    user_id: UUID
    full_name: str
    latitude: float
    longitude: float
    profession_tags: List[str] = []
    average_rating: float = 0.0
    is_online: bool = True


# ── Rating Schemas ────────────────────────────────────────────

class RatingCreateRequest(BaseModel):
    job_id: UUID
    rated_id: UUID
    stars: float = Field(..., ge=1.0, le=5.0)
    comment: Optional[str] = None
    tags: List[str] = []


class RatingResponse(BaseModel):
    id: UUID
    job_id: UUID
    rater_id: UUID
    rated_id: UUID
    stars: float
    comment: Optional[str] = None
    tags: List[str] = []
    created_at: datetime

    class Config:
        from_attributes = True


# ── Message Schemas ───────────────────────────────────────────

class MessageCreateRequest(BaseModel):
    receiver_id: UUID
    content: str = Field(..., min_length=1)
    attachment_url: Optional[str] = None
    attachment_type: Optional[str] = None


class MessageResponse(BaseModel):
    id: UUID
    sender_id: UUID
    receiver_id: UUID
    content: str
    attachment_url: Optional[str] = None
    attachment_type: Optional[str] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    user_id: UUID
    full_name: str
    avatar_url: Optional[str] = None
    last_message: str
    last_message_at: datetime
    unread_count: int = 0


# ── Notification Schemas ──────────────────────────────────────

class NotificationResponse(BaseModel):
    id: UUID
    type: NotificationType
    title: str
    body: Optional[str] = None
    is_read: bool
    action_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Audit Log Schemas ─────────────────────────────────────────

class AuditLogResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Admin Analytics ───────────────────────────────────────────

class DashboardStats(BaseModel):
    total_users: int
    total_employers: int
    total_employees: int
    total_jobs: int
    active_jobs: int
    completed_jobs: int
    total_tokens_sold: int
    total_revenue_usd: float
    online_workers: int


# ── Pagination ────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    size: int
    pages: int
