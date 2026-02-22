"""
Location & heatmap routes + WebSocket for real-time GPS.
"""

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas import LocationUpdateRequest, LocationResponse, WorkerMapResponse
from app.services.auth import get_current_user, require_role, decode_token
from app.services.location_service import update_user_location, get_nearby_workers, get_heatmap_data
from app.database import AsyncSessionLocal

router = APIRouter(prefix="/locations", tags=["Locations"])


@router.post("/update", response_model=LocationResponse)
async def update_location(
    req: LocationUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current GPS location (REST endpoint)."""
    loc = await update_user_location(db, current_user.id, req.latitude, req.longitude, req.accuracy)
    return LocationResponse(
        user_id=current_user.id,
        latitude=loc.latitude,
        longitude=loc.longitude,
        accuracy=loc.accuracy,
        created_at=loc.created_at,
    )


@router.get("/workers", response_model=list[WorkerMapResponse])
async def list_nearby_workers(
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius: float = Query(50.0),
    profession: str = Query(None),
    current_user: User = Depends(require_role(UserRole.EMPLOYER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Get nearby online workers for map display."""
    workers = await get_nearby_workers(db, latitude, longitude, radius, profession)
    return [WorkerMapResponse(**w) for w in workers]


@router.get("/heatmap")
async def heatmap(
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius: float = Query(100.0),
    current_user: User = Depends(require_role(UserRole.EMPLOYER, UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Get heatmap data for worker density."""
    return await get_heatmap_data(db, latitude, longitude, radius)


# ── WebSocket for real-time location streaming ───────────────

@router.websocket("/ws/{token}")
async def location_websocket(websocket: WebSocket, token: str):
    """
    WebSocket endpoint for real-time location updates.
    Workers send { lat, lng, accuracy } every 10-30 seconds.
    """
    await websocket.accept()
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    try:
        while True:
            data = await websocket.receive_text()
            parsed = json.loads(data)
            lat = parsed.get("latitude") or parsed.get("lat")
            lng = parsed.get("longitude") or parsed.get("lng")
            accuracy = parsed.get("accuracy")

            if lat and lng:
                async with AsyncSessionLocal() as db:
                    await update_user_location(db, user_id, lat, lng, accuracy)
                    await websocket.send_text(json.dumps({"status": "ok"}))
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close(code=4000, reason=str(e))
