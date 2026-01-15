"""
Conftest.py - Pytest's special file for shared test setup.

Fixtures = Reusable test dependencies (like database, HTTP client, etc.)
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from unittest.mock import AsyncMock, MagicMock, patch

from app.db import get_db, Base
from main import app
# Import models so SQLAlchemy knows about all tables
from app import models  # This loads all model classes


# ========== FIXTURE 1: Test Database Engine ==========
@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """
    Creates a test database engine for each test.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=NullPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# ========== FIXTURE 2: Test Database Session ==========
@pytest_asyncio.fixture
async def test_db(test_engine):
    """
    Creates a fresh database session for each test.
    """
    async_session_maker = async_sessionmaker(
        test_engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session


# ========== FIXTURE 3: HTTP Client ==========
@pytest_asyncio.fixture
async def client(test_engine):
    """
    Creates an HTTP client for making requests to your API.
    
    The client creates its own sessions through the overridden get_db.
    """
    # Create a session factory for this test
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # Override get_db to use our test database
    async def override_get_db():
        async with async_session_maker() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create HTTP client
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    # Cleanup
    app.dependency_overrides.clear()


# ========== FIXTURE 4: Mock Redis ==========
@pytest.fixture(autouse=True)
def mock_redis():
    """
    Mock Redis so tests don't need a real Redis server.
    
    autouse=True = Runs automatically for every test.
    
    This creates a fake in-memory Redis that acts like the real thing.
    """
    # Create a fake Redis with in-memory storage
    fake_redis_storage = {}
    
    def fake_get(key):
        return fake_redis_storage.get(key)
    
    def fake_set(key, value):
        fake_redis_storage[key] = value
        return True
    
    def fake_setex(key, seconds, value):
        fake_redis_storage[key] = value
        return True
    
    def fake_incr(key):
        current = int(fake_redis_storage.get(key, 0))
        fake_redis_storage[key] = str(current + 1)
        return current + 1
    
    def fake_expire(key, seconds):
        return True
    
    def fake_delete(key):
        fake_redis_storage.pop(key, None)
        return True
    
    def fake_flushdb():
        fake_redis_storage.clear()
        return True
    
    def fake_pipeline():
        # Mock pipeline object
        mock_pipeline = MagicMock()
        mock_pipeline.incr = MagicMock(return_value=None)
        mock_pipeline.expire = MagicMock(return_value=None)
        mock_pipeline.execute = MagicMock(return_value=[1, True])
        return mock_pipeline
    
    # Replace real Redis with our fake one
    with patch('app.cache.redis_client') as mock_redis_client:
        mock_redis_client.get = fake_get
        mock_redis_client.set = fake_set
        mock_redis_client.setex = fake_setex
        mock_redis_client.incr = fake_incr
        mock_redis_client.expire = fake_expire
        mock_redis_client.delete = fake_delete
        mock_redis_client.flushdb = fake_flushdb
        mock_redis_client.pipeline = fake_pipeline
        
        # Also patch in rate_limiter
        with patch('app.rate_limiter.redis_client', mock_redis_client):
            yield mock_redis_client
    
    # Cleanup
    fake_redis_storage.clear()


# ========== FIXTURE 5: Mock OpenAI ==========
@pytest.fixture
def mock_openai():
    """
    Mock OpenAI API so tests don't make real API calls.
    
    Usage in tests:
        async def test_create_goal(client, mock_openai):
            # OpenAI calls are automatically mocked!
    """
    fake_roadmap_response = {
        "title": "Learn Python Programming",
        "category": "Programming",
        "difficulty": "beginner",
        "roadmap": {
            "name": "Python Fundamentals Roadmap",
            "levels": [
                {
                    "order": 1,
                    "title": "Python Basics",
                    "description": "Learn fundamental Python concepts",
                    "topics": [
                        {"name": "Variables and Data Types", "completed": False},
                        {"name": "Control Flow (if/else, loops)", "completed": False},
                        {"name": "Functions", "completed": False}
                    ],
                    "xp_reward": 100
                },
                {
                    "order": 2,
                    "title": "Data Structures",
                    "description": "Master Python's built-in data structures",
                    "topics": [
                        {"name": "Lists and Tuples", "completed": False},
                        {"name": "Dictionaries", "completed": False},
                        {"name": "Sets", "completed": False}
                    ],
                    "xp_reward": 150
                }
            ]
        }
    }
    
    fake_quiz_response = {
        "questions": [
            {
                "id": 1,
                "question": "What is a variable in Python?",
                "options": [
                    {"text": "A container for storing data", "value": "A"},
                    {"text": "A type of loop", "value": "B"},
                    {"text": "A function", "value": "C"},
                    {"text": "A class", "value": "D"}
                ],
                "correct_answer": "A"
            },
            {
                "id": 2,
                "question": "Which keyword is used to define a function?",
                "options": [
                    {"text": "function", "value": "A"},
                    {"text": "def", "value": "B"},
                    {"text": "func", "value": "C"},
                    {"text": "define", "value": "D"}
                ],
                "correct_answer": "B"
            }
        ]
    }
    
    # Mock the generate_roadmap function
    async def fake_generate_roadmap(description):
        return fake_roadmap_response
    
    # Mock the generate_quiz function
    async def fake_generate_quiz(level_title, level_topics):
        return fake_quiz_response
    
    # Patch both functions
    with patch('app.ai_service.generate_roadmap', side_effect=fake_generate_roadmap), \
         patch('app.ai_service.generate_quiz_for_level', side_effect=fake_generate_quiz), \
         patch('app.goals.generate_roadmap', side_effect=fake_generate_roadmap), \
         patch('app.quizzes.generate_quiz_for_level', side_effect=fake_generate_quiz):
        yield {
            'roadmap': fake_roadmap_response,
            'quiz': fake_quiz_response
        }
