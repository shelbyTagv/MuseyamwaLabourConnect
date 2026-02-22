"""
Backend tests – auth, tokens, jobs.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Health Check ──────────────────────────────────────────────

@pytest.mark.anyio
async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


@pytest.mark.anyio
async def test_root(client: AsyncClient):
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "MuseyamwaLabourConnect" in data["name"]


# ── Auth Tests ────────────────────────────────────────────────

@pytest.mark.anyio
async def test_register_employer(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "test_employer@test.zw",
        "phone": "+263771999001",
        "password": "TestPass@123",
        "full_name": "Test Employer",
        "role": "employer",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["role"] == "employer"


@pytest.mark.anyio
async def test_register_employee(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "test_worker@test.zw",
        "phone": "+263772999001",
        "password": "TestPass@123",
        "full_name": "Test Worker",
        "role": "employee",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["user"]["role"] == "employee"


@pytest.mark.anyio
async def test_login(client: AsyncClient):
    # First register
    await client.post("/api/v1/auth/register", json={
        "email": "login_test@test.zw",
        "phone": "+263771999999",
        "password": "TestPass@123",
        "full_name": "Login Test",
        "role": "employer",
    })
    # Then login
    resp = await client.post("/api/v1/auth/login", json={
        "email": "login_test@test.zw",
        "password": "TestPass@123",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.anyio
async def test_login_wrong_password(client: AsyncClient):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "nonexistent@test.zw",
        "password": "wrong",
    })
    assert resp.status_code == 401


# ── Token Tests ───────────────────────────────────────────────

@pytest.mark.anyio
async def test_get_wallet(client: AsyncClient):
    # Register and get token
    reg = await client.post("/api/v1/auth/register", json={
        "email": "wallet_test@test.zw",
        "phone": "+263771888001",
        "password": "TestPass@123",
        "full_name": "Wallet Test",
        "role": "employer",
    })
    token = reg.json()["access_token"]

    resp = await client.get("/api/v1/tokens/wallet", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["balance"] == 0


# ── Job Tests ─────────────────────────────────────────────────

@pytest.mark.anyio
async def test_create_job_no_tokens(client: AsyncClient):
    """Creating a job without tokens should fail with 402."""
    reg = await client.post("/api/v1/auth/register", json={
        "email": "job_test@test.zw",
        "phone": "+263771777001",
        "password": "TestPass@123",
        "full_name": "Job Test",
        "role": "employer",
    })
    token = reg.json()["access_token"]

    resp = await client.post("/api/v1/jobs/", json={
        "title": "Test Job",
        "description": "A test job for the platform",
        "category": "Testing",
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 402  # Insufficient tokens


# ── Unauthorized Access ───────────────────────────────────────

@pytest.mark.anyio
async def test_unauthorized(client: AsyncClient):
    resp = await client.get("/api/v1/tokens/wallet")
    assert resp.status_code == 403  # No token provided
