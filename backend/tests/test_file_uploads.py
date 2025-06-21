"""
Tests for File Upload API endpoints
Tests file upload, validation, and MinIO integration
"""

import os
import pytest
import uuid
from typing import AsyncGenerator, Dict, Any
from unittest.mock import Mock, patch, AsyncMock
from io import BytesIO

from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from bson import ObjectId

from backend.main import app
from backend.models import init_models
from backend.models.user import User
from backend.models.session import Session
from backend.services.storage import StorageError


# Test database configuration
TEST_MONGODB_URL = os.getenv("MONGODB_URL_TEST", "mongodb://localhost:27017")
TEST_DATABASE_NAME = "test_promptly_files"


@pytest.fixture
async def test_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """
    Fixture providing a clean test database
    """
    client = AsyncIOMotorClient(TEST_MONGODB_URL, uuidRepresentation="standard")
    db = client[TEST_DATABASE_NAME]
    
    # Initialize indexes
    await init_models(db)
    
    yield db
    
    # Cleanup
    await db["sessions"].drop()
    await db["users"].drop()
    await db["files"].drop()
    client.close()


@pytest.fixture
async def test_client(test_db) -> AsyncGenerator[AsyncClient, None]:
    """
    Fixture providing test HTTP client with database override
    """
    from backend.core.database import get_database
    
    async def override_get_database():
        return test_db
    
    app.dependency_overrides[get_database] = override_get_database
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(test_db) -> User:
    """
    Fixture providing a test user in the database
    """
    user_data = {
        "_id": ObjectId(),
        "email": "test@example.com",
        "hashed_password": "hashed_password_123",
        "is_active": True,
        "is_superuser": False,
        "is_verified": True
    }
    
    await test_db["users"].insert_one(user_data)
    return User(**user_data)


@pytest.fixture
async def test_session(test_db, test_user: User) -> Session:
    """
    Fixture providing a test session in the database
    """
    session_data = {
        "_id": ObjectId(),
        "user_id": ObjectId(test_user.id),
        "title": "Test Session",
        "starter_prompt": "Test prompt",
        "max_questions": 10,
        "target_model": "gpt-4",
        "settings": {"contextSources": []},
        "status": "active"
    }
    
    await test_db["sessions"].insert_one(session_data)
    return Session(**session_data)


@pytest.fixture
async def auth_headers(test_client: AsyncClient, test_user: User) -> Dict[str, str]:
    """
    Fixture providing authentication headers for test requests
    """
    from backend.auth import current_active_user
    
    async def override_current_active_user():
        return test_user
    
    app.dependency_overrides[current_active_user] = override_current_active_user
    
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def mock_minio_client():
    """
    Fixture providing a mocked MinIO client
    """
    with patch('backend.services.storage.get_minio_client') as mock_get_client:
        mock_client = Mock()
        mock_client_instance = Mock()
        
        # Mock client methods
        mock_client_instance.upload_file.return_value = "test-object-key"
        mock_client_instance.get_presigned_url.return_value = "https://example.com/presigned-url"
        
        mock_client.return_value = mock_client_instance
        mock_get_client.return_value = mock_client_instance
        
        yield mock_client_instance


class TestFileUpload:
    """Test file upload endpoint"""
    
    @pytest.mark.asyncio
    async def test_upload_file_success(
        self, 
        test_client: AsyncClient, 
        auth_headers: Dict[str, str],
        mock_minio_client
    ):
        """Test successful file upload"""
        # Create test file content
        file_content = b"This is test file content"
        file_data = {
            "file": ("test.txt", BytesIO(file_content), "text/plain")
        }
        
        response = await test_client.post(
            "/files",
            files=file_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure
        assert "fileId" in data
        assert "url" in data
        assert "size" in data
        assert "mime" in data
        
        assert data["size"] == len(file_content)
        assert data["mime"] == "text/plain"
        assert data["url"] == "https://example.com/presigned-url"
        
        # Verify MinIO client was called
        mock_minio_client.upload_file.assert_called_once()
        mock_minio_client.get_presigned_url.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_file_with_session_link(
        self, 
        test_client: AsyncClient, 
        auth_headers: Dict[str, str],
        test_session: Session,
        mock_minio_client,
        test_db
    ):
        """Test file upload with session linking"""
        file_content = b"Session linked file content"
        file_data = {
            "file": ("session-file.pdf", BytesIO(file_content), "application/pdf")
        }
        
        response = await test_client.post(
            f"/files?session_id={test_session.id}",
            files=file_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["size"] == len(file_content)
        assert data["mime"] == "application/pdf"
        
        # Verify session was updated with context source
        updated_session = await test_db["sessions"].find_one({"_id": ObjectId(str(test_session.id))})
        assert updated_session is not None
        assert "contextSources" in updated_session["settings"]
        assert len(updated_session["settings"]["contextSources"]) == 1
        
        context_source = updated_session["settings"]["contextSources"][0]
        assert context_source["type"] == "file"
        assert context_source["fileId"] == data["fileId"]
        assert context_source["filename"] == "session-file.pdf"
        assert context_source["size"] == len(file_content)
        assert context_source["contentType"] == "application/pdf"
    
    @pytest.mark.asyncio
    async def test_upload_file_size_limit(
        self, 
        test_client: AsyncClient, 
        auth_headers: Dict[str, str]
    ):
        """Test file upload size limit (20 MB)"""
        # Create file content larger than 20 MB
        large_content = b"x" * (21 * 1024 * 1024)  # 21 MB
        file_data = {
            "file": ("large-file.txt", BytesIO(large_content), "text/plain")
        }
        
        response = await test_client.post(
            "/files",
            files=file_data,
            headers=auth_headers
        )
        
        assert response.status_code == 413
        data = response.json()
        assert "20 MB limit" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_upload_dangerous_file_type(
        self, 
        test_client: AsyncClient, 
        auth_headers: Dict[str, str]
    ):
        """Test rejection of dangerous file types"""
        dangerous_files = [
            ("virus.exe", "application/x-msdownload"),
            ("script.js", "application/javascript"),
            ("malware.bat", "application/x-msdos-program"),
            ("shell.sh", "text/x-shellscript"),
        ]
        
        for filename, content_type in dangerous_files:
            file_content = b"dangerous content"
            file_data = {
                "file": (filename, BytesIO(file_content), content_type)
            }
            
            response = await test_client.post(
                "/files",
                files=file_data,
                headers=auth_headers
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "File type not allowed" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_upload_no_file(
        self, 
        test_client: AsyncClient, 
        auth_headers: Dict[str, str]
    ):
        """Test upload without providing file"""
        response = await test_client.post(
            "/files",
            headers=auth_headers
        )
        
        assert response.status_code == 422
        data = response.json()
        assert "No file provided" in str(data["detail"])
    
    @pytest.mark.asyncio
    async def test_upload_invalid_session_id(
        self, 
        test_client: AsyncClient, 
        auth_headers: Dict[str, str],
        mock_minio_client
    ):
        """Test upload with invalid session ID"""
        file_content = b"Test content"
        file_data = {
            "file": ("test.txt", BytesIO(file_content), "text/plain")
        }
        
        # Use non-existent session ID
        fake_session_id = str(ObjectId())
        
        response = await test_client.post(
            f"/files?session_id={fake_session_id}",
            files=file_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Session not found" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_upload_storage_error(
        self, 
        test_client: AsyncClient, 
        auth_headers: Dict[str, str]
    ):
        """Test handling of storage service errors"""
        with patch('backend.services.storage.get_minio_client') as mock_get_client:
            mock_client = Mock()
            mock_client.upload_file.side_effect = StorageError("Storage unavailable", 503)
            mock_get_client.return_value = mock_client
            
            file_content = b"Test content"
            file_data = {
                "file": ("test.txt", BytesIO(file_content), "text/plain")
            }
            
            response = await test_client.post(
                "/files",
                files=file_data,
                headers=auth_headers
            )
            
            assert response.status_code == 503
            data = response.json()
            assert "Storage unavailable" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_upload_unauthorized(
        self, 
        test_client: AsyncClient
    ):
        """Test upload without authentication"""
        file_content = b"Test content"
        file_data = {
            "file": ("test.txt", BytesIO(file_content), "text/plain")
        }
        
        response = await test_client.post(
            "/files",
            files=file_data
        )
        
        assert response.status_code == 401


class TestFileInfo:
    """Test file info retrieval endpoint"""
    
    @pytest.mark.asyncio
    async def test_get_file_info_success(
        self,
        test_client: AsyncClient,
        auth_headers: Dict[str, str],
        test_user: User,
        test_db,
        mock_minio_client
    ):
        """Test successful file info retrieval"""
        # Insert test file metadata
        file_id = str(uuid.uuid4())
        file_metadata = {
            "file_id": file_id,
            "object_key": f"user-{test_user.id}/{file_id}-test.txt",
            "filename": "test.txt",
            "size": 100,
            "content_type": "text/plain",
            "uploaded_by": ObjectId(test_user.id),
            "uploaded_at": "2023-01-01T00:00:00Z"
        }
        
        await test_db["files"].insert_one(file_metadata)
        
        response = await test_client.get(
            f"/files/{file_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["fileId"] == file_id
        assert data["filename"] == "test.txt"
        assert data["size"] == 100
        assert data["contentType"] == "text/plain"
        assert data["url"] == "https://example.com/presigned-url"
        
        # Verify MinIO client was called for URL generation
        mock_minio_client.get_presigned_url.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_file_info_not_found(
        self,
        test_client: AsyncClient,
        auth_headers: Dict[str, str]
    ):
        """Test file info retrieval for non-existent file"""
        fake_file_id = str(uuid.uuid4())
        
        response = await test_client.get(
            f"/files/{fake_file_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "File not found" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_get_file_info_unauthorized(
        self,
        test_client: AsyncClient
    ):
        """Test file info retrieval without authentication"""
        fake_file_id = str(uuid.uuid4())
        
        response = await test_client.get(f"/files/{fake_file_id}")
        
        assert response.status_code == 401


class TestFilenameSanitization:
    """Test filename sanitization functionality"""
    
    def test_sanitize_dangerous_filename(self):
        """Test sanitization of dangerous filenames"""
        from backend.services.storage import sanitize_filename
        
        test_cases = [
            ("../../../etc/passwd", "etc_passwd"),
            ("file with spaces.txt", "file_with_spaces.txt"),
            ("file..with..dots.txt", "file_with_dots.txt"),
            ("file/with/slashes.txt", "file_with_slashes.txt"),
            ("file<>with|special:chars.txt", "file_with_special_chars.txt"),
            ("", "uploaded_file"),
            (".hidden", "uploaded_file.hidden"),
            ("a" * 300 + ".txt", "a" * 250 + ".txt"),  # Long filename
        ]
        
        for original, expected in test_cases:
            result = sanitize_filename(original)
            assert result == expected, f"Failed for '{original}': got '{result}', expected '{expected}'"
    
    def test_validate_file_type(self):
        """Test file type validation"""
        from backend.services.storage import validate_file_type
        
        # Safe file types
        safe_cases = [
            ("text/plain", "document.txt"),
            ("image/jpeg", "photo.jpg"),
            ("application/pdf", "document.pdf"),
            ("application/json", "data.json"),
        ]
        
        for content_type, filename in safe_cases:
            assert validate_file_type(content_type, filename) is True
        
        # Dangerous file types
        dangerous_cases = [
            ("application/x-msdownload", "virus.exe"),
            ("application/javascript", "script.js"),
            ("text/x-shellscript", "script.sh"),
            ("application/x-python-code", "script.py"),
            ("text/plain", "script.bat"),  # Dangerous extension
        ]
        
        for content_type, filename in dangerous_cases:
            assert validate_file_type(content_type, filename) is False 