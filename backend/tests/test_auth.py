from datetime import datetime, timedelta, timezone
import jwt
import pytest
from httpx import AsyncClient

from app.config import settings
from tests.conftest import TEST_USER_1_ID, create_token


@pytest.mark.asyncio
async def test_user_registration_success(client: AsyncClient):
    """User can register with valid email and password."""
    payload = {
        "email": "newuser@example.com",
        "password": "securepassword123",
        "name": "New User",
    }
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["name"] == "New User"
    assert "id" in data["user"]


@pytest.mark.asyncio
async def test_user_registration_duplicate_email(client: AsyncClient):
    """Registering an email that already exists must be rejected with 409 Conflict."""
    payload = {
        "email": "duplicate@example.com",
        "password": "password123",
    }
    first_res = await client.post("/api/auth/register", json=payload)
    assert first_res.status_code == 201

    dup_res = await client.post("/api/auth/register", json=payload)
    assert dup_res.status_code == 409
    assert "already exists" in dup_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_user_registration_invalid_email(client: AsyncClient):
    """Invalid email format must be rejected with 422."""
    payload = {
        "email": "not-an-email",
        "password": "password123",
    }
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_user_registration_short_password(client: AsyncClient):
    """Passwords shorter than 6 characters must be rejected with 422."""
    payload = {
        "email": "shortpass@example.com",
        "password": "123",
    }
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_user_login_success(client: AsyncClient):
    """User can log in with registered email and password."""
    # Register first
    await client.post(
        "/api/auth/register",
        json={"email": "loginuser@example.com", "password": "mypassword123", "name": "Login User"},
    )

    # Login
    response = await client.post(
        "/api/auth/login",
        json={"email": "loginuser@example.com", "password": "mypassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "loginuser@example.com"


@pytest.mark.asyncio
async def test_user_login_wrong_password(client: AsyncClient):
    """Login with wrong password must return 401."""
    await client.post(
        "/api/auth/register",
        json={"email": "wrongpwd@example.com", "password": "correctpassword"},
    )

    response = await client.post(
        "/api/auth/login",
        json={"email": "wrongpwd@example.com", "password": "incorrectpassword"},
    )
    assert response.status_code == 401
    assert "invalid email or password" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_user_login_unregistered_email(client: AsyncClient):
    """Login with unregistered email must return 401."""
    response = await client.post(
        "/api/auth/login",
        json={"email": "nonexistent@example.com", "password": "somepassword"},
    )
    assert response.status_code == 401
    assert "invalid email or password" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_missing_auth_token_rejected(client: AsyncClient):
    """Endpoints requiring authentication must reject unauthenticated requests with 401."""
    response = await client.get("/api/auth/me")
    assert response.status_code == 401
    assert "detail" in response.json()
    assert response.headers.get("WWW-Authenticate") == "Bearer"


@pytest.mark.asyncio
async def test_malformed_auth_token_rejected(client: AsyncClient):
    """Malformed bearer tokens must be rejected with 401."""
    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer not-a-valid-jwt-token"},
    )
    assert response.status_code == 401
    assert "Invalid authentication token" in response.json()["detail"]


@pytest.mark.asyncio
async def test_invalid_signature_rejected(client: AsyncClient):
    """Tokens signed with the wrong secret key must be rejected with 401."""
    payload = {
        "sub": TEST_USER_1_ID,
        "aud": "authenticated",
        "exp": int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()),
    }
    bogus_token = jwt.encode(payload, "wrong-secret-key-that-does-not-match", algorithm="HS256")

    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {bogus_token}"},
    )
    assert response.status_code == 401
    assert "Invalid authentication token" in response.json()["detail"]


@pytest.mark.asyncio
async def test_expired_token_rejected(client: AsyncClient):
    """Expired tokens must be rejected with 401."""
    expired_token = create_token(TEST_USER_1_ID, expires_in_hours=-2)

    response = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_valid_token_authenticated(auth_client_1: AsyncClient):
    """Valid tokens should successfully authenticate and return current user profile."""
    response = await auth_client_1.get("/api/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == TEST_USER_1_ID
    assert data["email"] == "alice@example.com"


@pytest.mark.asyncio
async def test_logout_endpoint(auth_client_1: AsyncClient):
    """Logout endpoint confirms session termination."""
    response = await auth_client_1.post("/api/auth/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"
