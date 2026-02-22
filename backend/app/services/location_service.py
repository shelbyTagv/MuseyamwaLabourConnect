"""
Location service – GPS proximity search and heatmap data.
"""

import math
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.location import Location
from app.models.user import User, UserRole
from app.models.profile import Profile


async def update_user_location(
    db: AsyncSession,
    user_id: UUID,
    latitude: float,
    longitude: float,
    accuracy: Optional[float] = None,
) -> Location:
    """Update (or insert) the current location for a user."""
    # Mark old locations as not current
    await db.execute(
        update(Location)
        .where(and_(Location.user_id == user_id, Location.is_current == True))
        .values(is_current=False)
    )

    loc = Location(
        user_id=user_id,
        latitude=latitude,
        longitude=longitude,
        accuracy=accuracy,
        is_current=True,
    )
    db.add(loc)
    await db.commit()
    await db.refresh(loc)
    return loc


async def get_nearby_workers(
    db: AsyncSession,
    latitude: float,
    longitude: float,
    radius_km: float = 50.0,
    profession: Optional[str] = None,
    limit: int = 100,
) -> List[dict]:
    """
    Find online workers near a GPS point.
    Returns list of worker dicts with location and profile info.
    """
    lat_range = radius_km / 111.0
    cos_lat = max(0.01, abs(math.cos(math.radians(latitude))))
    lng_range = radius_km / (111.0 * cos_lat)

    query = (
        select(User, Location, Profile)
        .join(Location, and_(Location.user_id == User.id, Location.is_current == True))
        .outerjoin(Profile, Profile.user_id == User.id)
        .where(
            User.role == UserRole.EMPLOYEE,
            User.is_online == True,
            User.is_active == True,
            User.is_suspended == False,
            Location.latitude.between(latitude - lat_range, latitude + lat_range),
            Location.longitude.between(longitude - lng_range, longitude + lng_range),
        )
    )

    if profession:
        query = query.where(Profile.profession_tags.any(profession))

    query = query.limit(limit)
    result = await db.execute(query)
    rows = result.all()

    workers = []
    for user, loc, profile in rows:
        workers.append({
            "user_id": str(user.id),
            "full_name": user.full_name,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "profession_tags": profile.profession_tags if profile else [],
            "average_rating": profile.average_rating if profile else 0,
            "is_online": user.is_online,
        })
    return workers


async def get_heatmap_data(
    db: AsyncSession,
    latitude: float,
    longitude: float,
    radius_km: float = 100.0,
) -> List[dict]:
    """
    Generate heatmap-ready data – clusters of online workers by location.
    """
    lat_range = radius_km / 111.0
    cos_lat = max(0.01, abs(math.cos(math.radians(latitude))))
    lng_range = radius_km / (111.0 * cos_lat)

    result = await db.execute(
        select(Location, Profile)
        .join(User, User.id == Location.user_id)
        .outerjoin(Profile, Profile.user_id == User.id)
        .where(
            Location.is_current == True,
            User.is_online == True,
            User.role == UserRole.EMPLOYEE,
            Location.latitude.between(latitude - lat_range, latitude + lat_range),
            Location.longitude.between(longitude - lng_range, longitude + lng_range),
        )
    )

    points = []
    for loc, profile in result.all():
        points.append({
            "lat": loc.latitude,
            "lng": loc.longitude,
            "intensity": 1,
            "profession_tags": profile.profession_tags if profile else [],
        })
    return points
