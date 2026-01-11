"""
Testing the /auth/register API endpoint.

These are INTEGRATION TESTS - they test the whole system working together
(database, API, validation, etc.)
"""
import pytest


@pytest.mark.asyncio  # Required for async test functions
async def test_register_new_user(client):
    """
    Test successful user registration.
    
    client = HTTP client fixture from conftest.py
    """
    # Make POST request to /auth/register
    response = await client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "securepassword123"
        }
    )
    
    # Check response
    assert response.status_code == 200
    
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data  # Should return user ID
    assert "password" not in data  # Should NOT return password!


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    """
    Test that registering the same email twice fails.
    """
    email = "duplicate@example.com"
    user_data = {"email": email, "password": "password123"}
    
    # Register first time - should succeed
    response1 = await client.post("/auth/register", json=user_data)
    assert response1.status_code == 200
    
    # Register second time with same email - should fail
    response2 = await client.post("/auth/register", json=user_data)
    assert response2.status_code == 400
    assert "already registered" in response2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_rate_limiting(client):
    """
    Test that rate limiting works (3 registrations per hour).
    
    This tests the check_rate_limit() function we built!
    """
    # Attempt 1 - should succeed
    response1 = await client.post(
        "/auth/register",
        json={"email": "user1@test.com", "password": "pass123"}
    )
    assert response1.status_code == 200
    
    # Attempt 2 - should succeed
    response2 = await client.post(
        "/auth/register",
        json={"email": "user2@test.com", "password": "pass123"}
    )
    assert response2.status_code == 200
    
    # Attempt 3 - should succeed
    response3 = await client.post(
        "/auth/register",
        json={"email": "user3@test.com", "password": "pass123"}
    )
    assert response3.status_code == 200
    
    # Attempt 4 - should be RATE LIMITED (429)
    response4 = await client.post(
        "/auth/register",
        json={"email": "user4@test.com", "password": "pass123"}
    )
    assert response4.status_code == 429
    assert "rate limit" in response4.json()["detail"].lower()
