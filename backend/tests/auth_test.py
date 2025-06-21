"""
Authentication tests for Promptly
Tests user registration, login, and JWT functionality
"""

import pytest
import asyncio
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient

from backend.main import app
from backend.core.database import db_manager


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db():
    """Create a test database connection."""
    # Use test database
    import os
    test_db_url = os.getenv("TEST_DATABASE_URL", "mongodb://admin:change-this-password-in-production@localhost:27017/promptly_test?authSource=admin")
    
    client = AsyncIOMotorClient(test_db_url)
    database = client.promptly_test
    
    yield database
    
    # Cleanup: drop test database
    await client.drop_database("promptly_test")
    client.close()


@pytest.fixture
async def client():
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def test_user_data():
    """Test user data for registration."""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User"
    }


class TestAuthentication:
    """Authentication test cases"""
    
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/ping")
        assert response.status_code == 200
        assert response.json() == {"ok": True}
    
    async def test_register_user(self, client: AsyncClient, test_user_data: dict):
        """Test user registration."""
        response = await client.post("/auth/register", json=test_user_data)
        assert response.status_code == 201
        
        user_data = response.json()
        assert user_data["email"] == test_user_data["email"]
        assert user_data["first_name"] == test_user_data["first_name"]
        assert user_data["is_active"] is True
        assert "id" in user_data
        assert "hashed_password" not in user_data  # Should not expose password
    
    async def test_register_duplicate_user(self, client: AsyncClient, test_user_data: dict):
        """Test registration with duplicate email."""
        # First registration
        await client.post("/auth/register", json=test_user_data)
        
        # Duplicate registration should fail
        response = await client.post("/auth/register", json=test_user_data)
        assert response.status_code == 400
    
    async def test_login_valid_credentials(self, client: AsyncClient, test_user_data: dict):
        """Test login with valid credentials."""
        # Register user first
        await client.post("/auth/register", json=test_user_data)
        
        # Login
        login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = await client.post("/auth/jwt/login", data=login_data)
        assert response.status_code == 200
        
        token_data = response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
    
    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        response = await client.post("/auth/jwt/login", data=login_data)
        assert response.status_code == 400
    
    async def test_protected_route_without_token(self, client: AsyncClient):
        """Test accessing protected route without token."""
        response = await client.get("/users/me")
        assert response.status_code == 401
    
    async def test_protected_route_with_token(self, client: AsyncClient, test_user_data: dict):
        """Test accessing protected route with valid token."""
        # Register and login
        await client.post("/auth/register", json=test_user_data)
        
        login_data = {
            "username": test_user_data["email"],
            "password": test_user_data["password"]
        }
        login_response = await client.post("/auth/jwt/login", data=login_data)
        token = login_response.json()["access_token"]
        
        # Access protected route
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get("/users/me", headers=headers)
        assert response.status_code == 200
        
        user_data = response.json()
        assert user_data["email"] == test_user_data["email"]


@pytest.mark.asyncio
async def test_password_hashing():
    """Test password hashing functionality."""
    from backend.models.user import password_manager
    
    password = "testpassword123"
    hashed = password_manager.hash_password(password)
    
    # Password should be hashed (different from original)
    assert hashed != password
    assert len(hashed) > 50  # Argon2 hashes are long
    
    # Verification should work
    assert password_manager.verify_password(password, hashed) is True
    assert password_manager.verify_password("wrongpassword", hashed) is False


if __name__ == "__main__":
    pytest.main([__file__]) 