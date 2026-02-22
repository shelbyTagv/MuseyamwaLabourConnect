"""
Notification service – creates notifications and broadcasts via WebSocket.
"""

from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType


# In-memory WebSocket connections (keyed by user_id string)
active_connections: dict[str, list] = {}


async def create_notification(
    db: AsyncSession,
    user_id: UUID,
    notification_type: NotificationType,
    title: str,
    body: Optional[str] = None,
    action_url: Optional[str] = None,
    reference_id: Optional[str] = None,
) -> Notification:
    """Persist a notification and try to push via WebSocket."""
    notif = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        body=body,
        action_url=action_url,
        reference_id=reference_id,
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)

    # Try WebSocket push
    await broadcast_to_user(str(user_id), {
        "type": "notification",
        "data": {
            "id": str(notif.id),
            "type": notification_type.value,
            "title": title,
            "body": body,
        },
    })

    return notif


async def broadcast_to_user(user_id: str, message: dict):
    """Send a JSON message to all active WebSocket connections for a user."""
    import json
    connections = active_connections.get(user_id, [])
    for ws in connections:
        try:
            await ws.send_text(json.dumps(message))
        except Exception:
            pass  # Connection may have closed


def register_connection(user_id: str, websocket):
    """Register a WebSocket connection for a user."""
    if user_id not in active_connections:
        active_connections[user_id] = []
    active_connections[user_id].append(websocket)


def unregister_connection(user_id: str, websocket):
    """Remove a WebSocket connection for a user."""
    if user_id in active_connections:
        active_connections[user_id] = [
            ws for ws in active_connections[user_id] if ws != websocket
        ]
