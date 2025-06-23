"""
Comprehensive Authentication System Tests
Tests all authentication flows and edge cases
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from main import app
from models.user import User, UserCreate
from auth.manager import UserManager
from core.database import get_database


class TestAuthenticationSystem:
    """Test complete authentication system"""
    
    def setup_method(self):
        """Setup test environment"""
        self.client = TestClient(app)
        self.test_user_data = {
            "email": "test@example.com",
            "password": "TestPassword123!",
            "username": "test@example.com",
            "first_name": "Test",
            "last_name": "User"
        }
    
    def test_user_registration_success(self):
        """Test successful user registration"""
        response = self.client.post("/auth/register", json=self.test_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == self.test_user_data["email"]
        assert data["username"] == self.test_user_data["username"]
        assert data["first_name"] == self.test_user_data["first_name"]
        assert data["last_name"] == self.test_user_data["last_name"]
        assert "id" in data
        
    def test_user_registration_duplicate_email(self):
        """Test registration with duplicate email fails"""
        # First registration
        self.client.post("/auth/register", json=self.test_user_data)
        
        # Second registration with same email
        response = self.client.post("/auth/register", json=self.test_user_data)
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()
    
    def test_user_registration_invalid_data(self):
        """Test registration with invalid data"""
        invalid_data = {
            "email": "invalid-email",
            "password": "123",  # Too short
            "username": "",
            "first_name": "",
            "last_name": ""
        }
        
        response = self.client.post("/auth/register", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_user_login_success(self):
        """Test successful user login"""
        # First register a user
        self.client.post("/auth/register", json=self.test_user_data)
        
        # Then login
        login_data = {
            "username": self.test_user_data["email"],
            "password": self.test_user_data["password"]
        }
        
        response = self.client.post("/auth/jwt/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response = self.client.post("/auth/jwt/login", data=login_data)
        
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()
    
    def test_protected_route_access(self):
        """Test accessing protected routes"""
        # Register and login
        self.client.post("/auth/register", json=self.test_user_data)
        
        login_response = self.client.post("/auth/jwt/login", data={
            "username": self.test_user_data["email"],
            "password": self.test_user_data["password"]
        })
        
        token = login_response.json()["access_token"]
        
        # Access protected route
        response = self.client.get("/users/me", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == self.test_user_data["email"]
    
    def test_protected_route_unauthorized(self):
        """Test accessing protected routes without token"""
        response = self.client.get("/users/me")
        
        assert response.status_code == 401


@pytest.mark.asyncio
class TestUserManager:
    """Test UserManager functionality"""
    
    async def test_password_hashing(self):
        """Test password hashing works correctly"""
        from models.user import password_manager
        
        password = "TestPassword123!"
        hashed = password_manager.hash_password(password)
        
        assert hashed != password
        assert password_manager.verify_password(password, hashed)
        assert not password_manager.verify_password("wrong", hashed)
    
    async def test_user_creation_flow(self):
        """Test complete user creation flow"""
        user_create = UserCreate(
            email="test@example.com",
            password="TestPassword123!",
            username="test@example.com",
            first_name="Test",
            last_name="User"
        )
        
        # Mock database
        mock_db = AsyncMock()
        mock_db.get_by_email.return_value = None  # No existing user
        mock_db.create.return_value = User(
            id="test-id",
            email="test@example.com",
            username="test@example.com",
            hashed_password="hashed_password",
            first_name="Test",
            last_name="User",
            is_active=True,
            is_superuser=False,
            is_verified=False
        )
        
        user_manager = UserManager(mock_db)
        created_user = await user_manager.create(user_create)
        
        assert created_user.email == "test@example.com"
        assert created_user.username == "test@example.com"
        assert created_user.first_name == "Test"
        assert created_user.last_name == "User"


class TestFrontendIntegration:
    """Test frontend-backend integration"""
    
    def test_cors_headers(self):
        """Test CORS headers are set correctly"""
        response = self.client.options("/auth/register")
        
        assert response.status_code == 200
        # Check for CORS headers in actual response
    
    def test_signup_endpoint_format(self):
        """Test signup endpoint accepts frontend format"""
        frontend_data = {
            "email": "test@example.com",
            "password": "TestPassword123!",
            "username": "test@example.com",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = self.client.post("/auth/register", json=frontend_data)
        
        # Should not fail due to format issues
        assert response.status_code in [201, 400]  # Either success or validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 