"""
Conftest.py - Pytest's special file for shared test setup.

Fixtures = Reusable test dependencies (like database, HTTP client, etc.)
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.db import get_db, Base
from app.cache import redis_client
from main import app
# Import models so SQLAlchemy knows about all tables
from app import models  # This loads all model classes


# ========== FIXTURE 1: Test Database ==========
@pytest_asyncio.fixture
async def test_db():
    """
    Creates a fresh database for each test.
    
    Why? Tests should be isolated - one test shouldn't affect another.
    
    This uses SQLite in-memory (fast, no files created).
    """
    # Step 1: Create engine (connection to database)
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",  # In-memory = fast, disappears after test
        poolclass=NullPool,  # Don't reuse connections
    )
    
    # Step 2: Create all tables (users, goals, etc.)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Step 3: Create session maker
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Step 4: Yield session to the test
    async with async_session() as session:
        yield session  # Test runs here
    
    # Step 5: Cleanup (runs after test completes)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# ========== FIXTURE 2: HTTP Client ==========
@pytest_asyncio.fixture
async def client(test_db):
    """
    Creates an HTTP client for making requests to your API.
    
    Usage in tests:
        response = await client.post("/auth/register", json={...})
        assert response.status_code == 201
    
    Note: This uses the test_db fixture (dependency injection).
    """
    # Override the real database with our test database
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create HTTP client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac  # Test uses this client
    
    # Cleanup
    app.dependency_overrides.clear()


# ========== FIXTURE 3: Clear Redis ==========
@pytest.fixture(autouse=True)
def clear_redis():
    """
    Clears Redis before each test.
    
    autouse=True = Runs automatically for every test.
    
    Why? Rate limits from one test shouldn't affect another.
    """
    try:
        redis_client.flushdb()
    except Exception:
        pass  # Redis might not be running
    
    yield  # Test runs here
    
    # Cleanup after test
    try:
        redis_client.flushdb()
    except Exception:
        pass
