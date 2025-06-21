"""
MinIO Storage Service for Promptly
Handles file uploads and object storage operations
"""

import os
import logging
from datetime import timedelta
from typing import Optional, BinaryIO
from functools import lru_cache

from minio import Minio
from minio.error import S3Error
from urllib3.exceptions import MaxRetryError

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Custom exception for storage operations"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class MinIOClient:
    """MinIO client wrapper with bucket management"""
    
    def __init__(self):
        self._client: Optional[Minio] = None
        self._bucket_name: str = os.getenv("MINIO_BUCKET", "promptly-files")
        self._url_expiry_hours: int = int(os.getenv("MINIO_URL_EXPIRY_HOURS", "24"))
    
    @property
    def client(self) -> Minio:
        """Get MinIO client instance (lazy initialization)"""
        if self._client is None:
            self._client = self._create_client()
            self._ensure_bucket_exists()
        return self._client
    
    def _create_client(self) -> Minio:
        """Create MinIO client from environment variables"""
        endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        
        if not all([endpoint, access_key, secret_key]):
            raise StorageError(
                "Missing MinIO configuration. Check MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY",
                status_code=500
            )
        
        try:
            client = Minio(
                endpoint=endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure
            )
            logger.info(f"✅ MinIO client initialized: {endpoint}")
            return client
        except Exception as e:
            logger.error(f"❌ Failed to initialize MinIO client: {e}")
            raise StorageError(f"Failed to initialize storage client: {str(e)}", status_code=500)
    
    def _ensure_bucket_exists(self):
        """Ensure the bucket exists (create if missing)"""
        try:
            if not self.client.bucket_exists(self._bucket_name):
                self.client.make_bucket(self._bucket_name)
                logger.info(f"✅ Created MinIO bucket: {self._bucket_name}")
            else:
                logger.info(f"✅ MinIO bucket exists: {self._bucket_name}")
        except S3Error as e:
            logger.error(f"❌ Failed to ensure bucket exists: {e}")
            raise StorageError(f"Failed to access storage bucket: {str(e)}", status_code=500)
        except MaxRetryError as e:
            logger.error(f"❌ MinIO connection failed: {e}")
            raise StorageError("Storage service unavailable", status_code=503)
    
    def upload_file(
        self,
        object_key: str,
        data: BinaryIO,
        size: int,
        content_type: str = "application/octet-stream"
    ) -> str:
        """
        Upload file to MinIO bucket
        
        Args:
            object_key: S3 object key for the file
            data: File data stream
            size: File size in bytes
            content_type: MIME type of the file
            
        Returns:
            Object key of uploaded file
            
        Raises:
            StorageError: If upload fails
        """
        try:
            # Upload with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.client.put_object(
                        bucket_name=self._bucket_name,
                        object_name=object_key,
                        data=data,
                        length=size,
                        content_type=content_type
                    )
                    logger.info(f"✅ File uploaded: {object_key} ({size} bytes)")
                    return object_key
                except S3Error as e:
                    if attempt == max_retries - 1:
                        raise e
                    logger.warning(f"⚠️  Upload attempt {attempt + 1} failed, retrying: {e}")
                    
        except S3Error as e:
            logger.error(f"❌ Failed to upload file {object_key}: {e}")
            raise StorageError(f"Failed to upload file: {str(e)}", status_code=500)
        except MaxRetryError as e:
            logger.error(f"❌ MinIO connection failed during upload: {e}")
            raise StorageError("Storage service unavailable", status_code=503)
    
    def get_presigned_url(self, object_key: str) -> str:
        """
        Generate presigned GET URL for file access
        
        Args:
            object_key: S3 object key
            
        Returns:
            Presigned URL valid for configured hours
            
        Raises:
            StorageError: If URL generation fails
        """
        try:
            url = self.client.presigned_get_object(
                bucket_name=self._bucket_name,
                object_name=object_key,
                expires=timedelta(hours=self._url_expiry_hours)
            )
            logger.info(f"✅ Generated presigned URL for {object_key} (expires in {self._url_expiry_hours}h)")
            return url
        except S3Error as e:
            logger.error(f"❌ Failed to generate presigned URL for {object_key}: {e}")
            raise StorageError(f"Failed to generate file access URL: {str(e)}", status_code=500)
    
    def delete_file(self, object_key: str) -> None:
        """
        Delete file from MinIO bucket
        
        Args:
            object_key: S3 object key to delete
            
        Raises:
            StorageError: If deletion fails
        """
        try:
            self.client.remove_object(self._bucket_name, object_key)
            logger.info(f"✅ File deleted: {object_key}")
        except S3Error as e:
            logger.error(f"❌ Failed to delete file {object_key}: {e}")
            raise StorageError(f"Failed to delete file: {str(e)}", status_code=500)


@lru_cache(maxsize=1)
def get_minio_client() -> MinIOClient:
    """Get singleton MinIO client instance"""
    return MinIOClient()


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for S3 storage
    """
    import re
    import unicodedata
    
    # Normalize unicode characters
    filename = unicodedata.normalize('NFKD', filename)
    
    # Remove dangerous characters, keep alphanumeric, dots, hyphens, underscores
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    
    # Remove multiple consecutive underscores/dots
    filename = re.sub(r'[_\.]{2,}', '_', filename)
    
    # Ensure not empty and not too long
    if not filename or filename.startswith('.'):
        filename = 'uploaded_file' + filename
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext
    
    return filename


def validate_file_type(content_type: str, filename: str) -> bool:
    """
    Validate file type against allowed MIME types
    
    Args:
        content_type: MIME type from upload
        filename: Original filename
        
    Returns:
        True if file type is allowed
    """
    # Dangerous MIME types to reject
    dangerous_types = {
        'application/x-msdownload',
        'application/x-executable',
        'application/x-sharedlib',
        'application/x-msdos-program',
        'application/vnd.microsoft.portable-executable',
        'text/x-script.python',
        'application/x-python-code',
        'text/x-shellscript',
        'application/javascript',
        'text/javascript'
    }
    
    # Dangerous extensions
    dangerous_extensions = {
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
        '.sh', '.py', '.pl', '.php', '.asp', '.aspx', '.jsp'
    }
    
    if content_type.lower() in dangerous_types:
        return False
    
    _, ext = os.path.splitext(filename.lower())
    if ext in dangerous_extensions:
        return False
    
    return True 