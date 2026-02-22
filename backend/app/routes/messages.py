"""
Messaging / Chat routes + WebSocket for real-time messaging.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select, func, or_, and_, case
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.database import get_db, AsyncSessionLocal
from app.models.user import User
from app.models.message import Message
from app.schemas import MessageCreateRequest, MessageResponse, ConversationResponse
from app.services.auth import get_current_user, decode_token
from app.services.notification_service import (
    create_notification, register_connection, unregister_connection, broadcast_to_user,
)
from app.models.notification import NotificationType
from app.services.token_service import deduct_tokens
from app.config import settings

router = APIRouter(prefix="/messages", tags=["Messages"])


@router.post("/", response_model=MessageResponse, status_code=201)
async def send_message(
    req: MessageCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a chat message (costs tokens)."""
    # Deduct tokens for sending a message
    await deduct_tokens(
        db, current_user.id, settings.MESSAGE_TOKEN_COST,
        description=f"Message to user",
    )

    msg = Message(
        sender_id=current_user.id,
        receiver_id=req.receiver_id,
        content=req.content,
        attachment_url=req.attachment_url,
        attachment_type=req.attachment_type,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    # Push via WebSocket
    await broadcast_to_user(str(req.receiver_id), {
        "type": "message",
        "data": {
            "id": str(msg.id),
            "sender_id": str(current_user.id),
            "content": msg.content,
            "created_at": msg.created_at.isoformat(),
        },
    })

    # Also create notification
    await create_notification(
        db, req.receiver_id, NotificationType.MESSAGE,
        title=f"New message from {current_user.full_name}",
        body=msg.content[:100],
        reference_id=str(msg.id),
    )

    return MessageResponse.model_validate(msg)


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all conversation threads for the current user."""
    # Get distinct conversation partners
    from sqlalchemy import union_all, literal_column

    # Find all unique users the current user has chatted with
    sent_to = select(Message.receiver_id.label("partner_id")).where(Message.sender_id == current_user.id)
    recv_from = select(Message.sender_id.label("partner_id")).where(Message.receiver_id == current_user.id)
    partners_q = union_all(sent_to, recv_from).subquery()
    partner_ids_q = select(func.distinct(partners_q.c.partner_id))
    partner_ids_result = await db.execute(partner_ids_q)
    partner_ids = [row[0] for row in partner_ids_result.all()]

    conversations = []
    for pid in partner_ids:
        # Last message
        last_msg_q = (
            select(Message)
            .where(
                or_(
                    and_(Message.sender_id == current_user.id, Message.receiver_id == pid),
                    and_(Message.sender_id == pid, Message.receiver_id == current_user.id),
                )
            )
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        result = await db.execute(last_msg_q)
        last_msg = result.scalar_one_or_none()

        # Unread count
        unread_q = select(func.count()).where(
            Message.sender_id == pid,
            Message.receiver_id == current_user.id,
            Message.is_read == False,
        )
        unread_result = await db.execute(unread_q)
        unread = unread_result.scalar() or 0

        # Partner info
        partner_q = await db.execute(select(User).where(User.id == pid))
        partner = partner_q.scalar_one_or_none()

        if partner and last_msg:
            conversations.append(ConversationResponse(
                user_id=pid,
                full_name=partner.full_name,
                last_message=last_msg.content[:100],
                last_message_at=last_msg.created_at,
                unread_count=unread,
            ))

    conversations.sort(key=lambda c: c.last_message_at, reverse=True)
    return conversations


@router.get("/{partner_id}", response_model=list[MessageResponse])
async def get_messages(
    partner_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get messages between current user and a partner."""
    query = (
        select(Message)
        .where(
            or_(
                and_(Message.sender_id == current_user.id, Message.receiver_id == partner_id),
                and_(Message.sender_id == partner_id, Message.receiver_id == current_user.id),
            )
        )
        .order_by(Message.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(query)
    messages = result.scalars().all()

    # Mark received messages as read
    for msg in messages:
        if msg.receiver_id == current_user.id and not msg.is_read:
            msg.is_read = True
    await db.commit()

    return [MessageResponse.model_validate(m) for m in reversed(messages)]


# ── WebSocket for real-time chat ──────────────────────────────

@router.websocket("/ws/{token}")
async def chat_websocket(websocket: WebSocket, token: str):
    """Real-time chat WebSocket. Also receives notifications."""
    await websocket.accept()
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    register_connection(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            parsed = json.loads(data)
            receiver_id = parsed.get("receiver_id")
            content = parsed.get("content")

            if receiver_id and content:
                async with AsyncSessionLocal() as db:
                    msg = Message(
                        sender_id=user_id,
                        receiver_id=receiver_id,
                        content=content,
                    )
                    db.add(msg)
                    await db.commit()
                    await db.refresh(msg)

                    # Broadcast to receiver
                    await broadcast_to_user(receiver_id, {
                        "type": "message",
                        "data": {
                            "id": str(msg.id),
                            "sender_id": user_id,
                            "content": content,
                            "created_at": msg.created_at.isoformat(),
                        },
                    })
    except WebSocketDisconnect:
        pass
    finally:
        unregister_connection(user_id, websocket)
