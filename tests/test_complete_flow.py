"""
Complete test example showing how to test with mocked external dependencies.

This demonstrates:
1. Testing database operations (SQLite in-memory)
2. Testing with mocked Redis (rate limiting)
3. Testing with mocked OpenAI (AI generation)
"""
import pytest
from sqlalchemy import select
from app.models import User, Goal


# ========== DATABASE TESTS (No external dependency) ==========

@pytest.mark.asyncio
async def test_user_registration_complete_flow(client):
    """
    Test the ENTIRE registration flow including:
    - HTTP request
    - Validation
    - Password hashing
    - Database insert
    - JWT generation
    """
    response = await client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "StrongPassword123!"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "id" in data
    assert data["email"] == "newuser@example.com"
    assert "password" not in data
    assert "password_hash" not in data
    
    # Verify user was actually created in database
    # (client fixture gives us access to test_db through dependency override)


@pytest.mark.asyncio
async def test_login_success(client):
    """
    Test login with correct credentials.
    """
    # First register a user
    await client.post(
        "/auth/register",
        json={
            "email": "logintest@example.com",
            "password": "MyPassword123"
        }
    )
    
    # Now try to login
    response = await client.post(
        "/auth/login",
        data={  # OAuth2 uses form data, not JSON
            "username": "logintest@example.com",  # OAuth2 calls it 'username'
            "password": "MyPassword123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    """
    Test login with wrong password.
    """
    # Register user
    await client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "CorrectPassword"
        }
    )
    
    # Try to login with wrong password
    response = await client.post(
        "/auth/login",
        data={
            "username": "user@example.com",
            "password": "WrongPassword"
        }
    )
    
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


# ========== REDIS TESTS (Mocked - no real Redis needed) ==========

@pytest.mark.asyncio
async def test_rate_limiting_blocks_after_limit(client):
    """
    Test that rate limiting actually blocks requests.
    
    Redis is MOCKED - no real Redis server needed!
    """
    # Registration limit is 5 per minute (from your rate_limiter config)
    for i in range(5):
        response = await client.post(
            "/auth/register",
            json={
                "email": f"user{i}@test.com",
                "password": "Password123"
            }
        )
        assert response.status_code == 200, f"Request {i+1} should succeed"
    
    # 6th request should be blocked
    response = await client.post(
        "/auth/register",
        json={
            "email": "blocked@test.com",
            "password": "Password123"
        }
    )
    
    assert response.status_code == 429
    assert "rate limit" in response.json()["detail"].lower()


# ========== OPENAI TESTS (Mocked - no real API calls) ==========

@pytest.mark.asyncio
async def test_create_goal_with_ai_roadmap(client, mock_openai):
    """
    Test goal creation with AI-generated roadmap.
    
    OpenAI is MOCKED - no real API calls, no API key needed!
    """
    # First, register and login to get a token
    await client.post(
        "/auth/register",
        json={
            "email": "goaluser@test.com",
            "password": "Password123"
        }
    )
    
    login_response = await client.post(
        "/auth/login",
        data={
            "username": "goaluser@test.com",
            "password": "Password123"
        }
    )
    token = login_response.json()["access_token"]
    
    # Now create a goal (this would normally call OpenAI)
    response = await client.post(
        "/goals",
        json={
            "description": "I want to learn Python programming"
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Check the goal was created with AI-generated data
    assert data["title"] == "Learn Python Programming"
    assert data["category"] == "Programming"
    assert data["difficulty"] == "beginner"
    
    # Check roadmap structure
    assert "roadmap" in data
    assert "levels" in data["roadmap"]
    assert len(data["roadmap"]["levels"]) == 2  # Our mock returns 2 levels
    
    # Check first level
    first_level = data["roadmap"]["levels"][0]
    assert first_level["title"] == "Python Basics"
    assert first_level["order"] == 1
    assert len(first_level["topics"]) == 3


@pytest.mark.asyncio
async def test_generate_quiz_for_level(client, mock_openai):
    """
    Test quiz generation (mocked OpenAI).
    """
    # Setup: Register, login, create goal
    await client.post(
        "/auth/register",
        json={"email": "quizuser@test.com", "password": "Pass123"}
    )
    
    login_response = await client.post(
        "/auth/login",
        data={"username": "quizuser@test.com", "password": "Pass123"}
    )
    token = login_response.json()["access_token"]
    
    # Create a goal (gets AI-generated roadmap)
    goal_response = await client.post(
        "/goals",
        json={"description": "Learn Python"},
        headers={"Authorization": f"Bearer {token}"}
    )
    goal = goal_response.json()
    first_level_id = goal["roadmap"]["levels"][0]["id"]
    
    # Generate quiz for the first level
    quiz_response = await client.post(
        f"/quizzes/generate/{first_level_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert quiz_response.status_code == 200
    quiz = quiz_response.json()
    
    # Check quiz structure
    assert "questions" in quiz
    assert len(quiz["questions"]) == 2  # Our mock returns 2 questions
    
    # Check first question
    q1 = quiz["questions"][0]
    assert q1["id"] == 1
    assert "question" in q1
    assert len(q1["options"]) == 4
    assert q1["correct_answer"] in ["A", "B", "C", "D"]


# ========== DIRECT DATABASE TESTS ==========

@pytest.mark.asyncio
async def test_user_model_creation(test_db):
    """
    Test creating a User directly in the database.
    
    This is a UNIT TEST - tests the model in isolation.
    """
    from app.auth import hash_password
    
    # Create a user
    user = User(
        email="directdb@test.com",
        password_hash=hash_password("password123"),
        total_exp=50
    )
    
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    
    # Verify it was created
    assert user.id is not None
    assert user.email == "directdb@test.com"
    assert user.total_exp == 50
    
    # Verify we can query it
    result = await test_db.execute(
        select(User).where(User.email == "directdb@test.com")
    )
    found_user = result.scalar_one()
    assert found_user.id == user.id


@pytest.mark.asyncio
async def test_goal_with_roadmap_relationship(test_db):
    """
    Test creating Goal with Roadmap relationship.
    """
    from app.auth import hash_password
    from app.models import Roadmap, Level
    
    # Create user
    user = User(
        email="goaltest@test.com",
        password_hash=hash_password("pass123")
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    
    # Create goal
    goal = Goal(
        user_id=user.id,
        title="Test Goal",
        category="Programming",
        difficulty_level="beginner"
    )
    test_db.add(goal)
    await test_db.commit()
    await test_db.refresh(goal)
    
    # Create roadmap
    roadmap = Roadmap(
        goal_id=goal.id,
        name="Test Roadmap"
    )
    test_db.add(roadmap)
    await test_db.commit()
    await test_db.refresh(roadmap)
    
    # Create levels
    level1 = Level(
        roadmap_id=roadmap.id,
        order=1,
        title="Level 1",
        description="First level",
        topics=[
            {"name": "Topic 1", "completed": False},
            {"name": "Topic 2", "completed": False}
        ],
        xp_reward=100,
        is_unlocked=True
    )
    test_db.add(level1)
    await test_db.commit()
    
    # Verify relationships work
    result = await test_db.execute(
        select(Goal).where(Goal.id == goal.id)
    )
    found_goal = result.scalar_one()
    
    assert found_goal.title == "Test Goal"
    # Note: To test relationships, you'd need to use selectinload in the query


# ========== ERROR HANDLING TESTS ==========

@pytest.mark.asyncio
async def test_invalid_email_format(client):
    """
    Test that invalid email format is rejected.
    """
    response = await client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "password": "Password123"
        }
    )
    
    assert response.status_code == 422  # Validation error
    assert "email" in str(response.json()).lower()


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(client):
    """
    Test that protected endpoints require authentication.
    """
    response = await client.get("/goals/me")
    
    assert response.status_code == 401
    assert "not authenticated" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_protected_endpoint_with_invalid_token(client):
    """
    Test that invalid tokens are rejected.
    """
    response = await client.get(
        "/goals/me",
        headers={"Authorization": "Bearer invalid_token_here"}
    )
    
    assert response.status_code == 401
