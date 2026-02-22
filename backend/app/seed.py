"""
Seed data script – creates sample employers, employees, jobs, and tokens for development/testing.
Run: python -m app.seed
"""

import asyncio
import random
from datetime import datetime, timedelta

from app.database import engine, Base, AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.profile import Profile
from app.models.token import TokenWallet, TokenTransaction, TransactionType
from app.models.job import Job, JobStatus
from app.models.location import Location
from app.models.rating import Rating
from app.services.auth import hash_password

# Harare coordinates center
HARARE_LAT = -17.8252
HARARE_LNG = 31.0335


SAMPLE_EMPLOYERS = [
    {"full_name": "Tinashe Moyo", "email": "tinashe@employer.co.zw", "phone": "+263771000001"},
    {"full_name": "Grace Mutasa", "email": "grace@employer.co.zw", "phone": "+263771000002"},
    {"full_name": "Tapiwa Chigumba", "email": "tapiwa@employer.co.zw", "phone": "+263771000003"},
]

SAMPLE_EMPLOYEES = [
    {"full_name": "Blessing Nyathi", "email": "blessing@worker.co.zw", "phone": "+263772000001",
     "skills": ["plumbing", "electrical"], "tags": ["Plumber", "Electrician"]},
    {"full_name": "Kudakwashe Dube", "email": "kuda@worker.co.zw", "phone": "+263772000002",
     "skills": ["carpentry", "painting"], "tags": ["Carpenter", "Painter"]},
    {"full_name": "Rumbidzai Mhandu", "email": "rumbi@worker.co.zw", "phone": "+263772000003",
     "skills": ["cleaning", "gardening"], "tags": ["House Cleaner", "Gardener"]},
    {"full_name": "Farai Chimba", "email": "farai@worker.co.zw", "phone": "+263772000004",
     "skills": ["masonry", "tiling"], "tags": ["Mason", "Tiler"]},
    {"full_name": "Tendai Makoni", "email": "tendai@worker.co.zw", "phone": "+263772000005",
     "skills": ["welding", "metalwork"], "tags": ["Welder"]},
]

SAMPLE_JOBS = [
    {"title": "Fix bathroom plumbing", "description": "Leaking pipe in bathroom needs urgent repair. Tools provided.",
     "category": "Plumbing", "budget_min": 20, "budget_max": 50},
    {"title": "Paint living room", "description": "Large living room needs fresh coat of paint. About 30 sq meters.",
     "category": "Painting", "budget_min": 40, "budget_max": 80},
    {"title": "Garden maintenance", "description": "Weekly garden maintenance including lawn mowing and hedge trimming.",
     "category": "Gardening", "budget_min": 15, "budget_max": 30},
    {"title": "Build kitchen cabinet", "description": "Custom kitchen cabinet, hardwood, 2m x 1m dimensions.",
     "category": "Carpentry", "budget_min": 100, "budget_max": 200},
    {"title": "House deep cleaning", "description": "Full deep cleaning of 4-bedroom house. Cleaning supplies provided.",
     "category": "Cleaning", "budget_min": 25, "budget_max": 40},
]


async def seed():
    print("🌱 Starting seed...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        employer_ids = []
        employee_ids = []

        # ── Create employers ──
        for emp_data in SAMPLE_EMPLOYERS:
            user = User(
                email=emp_data["email"], phone=emp_data["phone"],
                password_hash=hash_password("Password@123"),
                full_name=emp_data["full_name"], role=UserRole.EMPLOYER,
                is_verified=True, is_active=True,
            )
            db.add(user)
            await db.flush()
            employer_ids.append(user.id)

            db.add(Profile(user_id=user.id, bio=f"Employer in Harare", city="Harare"))
            db.add(TokenWallet(user_id=user.id, balance=50, total_purchased=50))

        # ── Create employees ──
        for emp_data in SAMPLE_EMPLOYEES:
            user = User(
                email=emp_data["email"], phone=emp_data["phone"],
                password_hash=hash_password("Password@123"),
                full_name=emp_data["full_name"], role=UserRole.EMPLOYEE,
                is_verified=True, is_active=True, is_online=True,
            )
            db.add(user)
            await db.flush()
            employee_ids.append(user.id)

            db.add(Profile(
                user_id=user.id, bio=f"Skilled worker in Harare",
                city="Harare", skills=emp_data["skills"],
                profession_tags=emp_data["tags"],
                experience_years=random.randint(1, 10),
                hourly_rate=random.uniform(5, 25),
                average_rating=round(random.uniform(3.5, 5.0), 1),
                total_ratings=random.randint(5, 50),
            ))
            db.add(TokenWallet(user_id=user.id, balance=20, total_purchased=20))

            # GPS location near Harare
            db.add(Location(
                user_id=user.id,
                latitude=HARARE_LAT + random.uniform(-0.05, 0.05),
                longitude=HARARE_LNG + random.uniform(-0.05, 0.05),
                is_current=True,
            ))

        # ── Create jobs ──
        for i, job_data in enumerate(SAMPLE_JOBS):
            employer_id = employer_ids[i % len(employer_ids)]
            lat = HARARE_LAT + random.uniform(-0.03, 0.03)
            lng = HARARE_LNG + random.uniform(-0.03, 0.03)

            job = Job(
                title=job_data["title"], description=job_data["description"],
                category=job_data["category"],
                latitude=lat, longitude=lng,
                location_name="Harare",
                budget_min=job_data["budget_min"], budget_max=job_data["budget_max"],
                employer_id=employer_id, status=JobStatus.REQUESTED,
                token_cost=2,
            )
            db.add(job)

        await db.commit()
        print(f"✅ Created {len(employer_ids)} employers, {len(employee_ids)} employees, {len(SAMPLE_JOBS)} jobs")
        print("🎉 Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
