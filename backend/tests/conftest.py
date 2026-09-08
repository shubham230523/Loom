import asyncio
import pytest
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.database.session import Base, get_db
from backend.app.services.redis import get_redis
from backend.app.config import settings

# Use the test database URL from environment (provided by pytest-env/pytest.ini)
TEST_DATABASE_URL = settings.DATABASE_URL

engine_test = create_async_engine(TEST_DATABASE_URL, future=True, poolclass=NullPool)
TestingSessionLocal = async_sessionmaker(
    bind=engine_test,
    class_=AsyncSession,
    expire_on_commit=False,
)

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Create database tables once for the test session."""
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated database session for a test."""
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()
        await session.close()

@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an authenticated (or unauthenticated) TestClient."""

    async def override_get_db():
        yield db_session

    async def override_get_redis():
        return None

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest.fixture
def mock_github(mocker):
    """Fixture to mock GitHub service calls."""
    return mocker.patch("backend.app.github.service.github_service")

@pytest.fixture
def mock_ai(mocker):
    """Fixture to mock AI Gateway calls."""
    return mocker.patch("backend.app.ai.gateway.ai_gateway")
