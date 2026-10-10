import asyncio
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator
import jwt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.config import settings

# Force test configuration
settings.ENVIRONMENT = "testing"
settings.JWT_SECRET = "test-secret-key-32-characters-minimum-for-hs256!!"
settings.JWT_ALGORITHM = "HS256"
settings.GROQ_API_KEY = "gsk_test_mock_groq_key_for_unit_tests"
settings.TAVILY_API_KEY = "tvly-test_mock_tavily_key_for_unit_tests"

from app.database.mongodb import mongodb_manager
from app.dependencies import get_db
from app.main import app
from app.services.conversation_service import conversation_service
from app.services.user_service import user_service
from tests.mock_mongo import MockMongoDBManager

TEST_USER_1_ID = "00000000-0000-0000-0000-000000000001"
TEST_USER_2_ID = "00000000-0000-0000-0000-000000000002"


def create_token(
    user_id: str,
    email: str = "test@example.com",
    role: str = "authenticated",
    expires_in_hours: int = 24,
) -> str:
    """Generate a test HS256 JWT access token."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "aud": "authenticated",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=expires_in_hours)).timestamp()),
    }
    return jwt.encode(payload, settings.effective_jwt_secret, algorithm="HS256")


@pytest.fixture
def mock_db() -> MockMongoDBManager:
    """Provide a fresh isolated in-memory mock database."""
    manager = MockMongoDBManager()
    # Inject into global singleton and services
    conversation_service._db = manager
    user_service._db = manager
    app.dependency_overrides[get_db] = lambda: manager
    yield manager
    manager.clear()
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def token_user1() -> str:
    return create_token(TEST_USER_1_ID, email="alice@example.com")


@pytest.fixture
def token_user2() -> str:
    return create_token(TEST_USER_2_ID, email="bob@example.com")


@pytest_asyncio.fixture
async def client(mock_db: MockMongoDBManager) -> AsyncGenerator[AsyncClient, None]:
    """Base HTTP test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_client_1(
    client: AsyncClient, token_user1: str
) -> AsyncGenerator[AsyncClient, None]:
    """Authenticated client as User 1."""
    client.headers.update({"Authorization": f"Bearer {token_user1}"})
    yield client


@pytest_asyncio.fixture
async def auth_client_2(
    mock_db: MockMongoDBManager, token_user2: str
) -> AsyncGenerator[AsyncClient, None]:
    """Authenticated client as User 2."""
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token_user2}"},
    ) as ac:
        yield ac
