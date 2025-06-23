"""
File Upload API endpoints for Promptly
Handles secure file uploads with MinIO integration
"""

import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, status
from fastapi.concurrency import run_in_threadpool
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from auth import current_active_user
from models.user import User
from core.database import get_database
from core.ratelimit import limiter, DEFAULT_RATE_LIMIT
from services.storage import (
    get_minio_client, 
    StorageError, 
    sanitize_filename, 
    validate_file_type
)

router = APIRouter(prefix="/files", tags=["files"])
logger = logging.getLogger(__name__)

# File upload limits
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
ALLOWED_UPLOAD_SIZE = MAX_FILE_SIZE


class FileUploadResponse:
    """Response model for file upload"""
    def __init__(self, file_id: str, url: str, size: int, mime: str):
        self.file_id = file_id
        self.url = url
        self.size = size
        self.mime = mime
    
    def dict(self) -> Dict[str, Any]:
        return {
            "fileId": self.file_id,
            "url": self.url,
            "size": self.size,
            "mime": self.mime
        }


@router.post(
    "",
    summary="Upload file",
    description="Upload a file to MinIO storage and get a presigned URL for access",
    responses={
        201: {
            "description": "File uploaded successfully",
            "content": {
                "application/json": {
                    "example": {
                        "fileId": "550e8400-e29b-41d4-a716-446655440000",
                        "url": "https://minio:9000/promptly-files/session-id/file-id-filename.pdf?X-Amz-Algorithm=...",
                        "size": 12345,
                        "mime": "application/pdf"
                    }
                }
            }
        },
        400: {"description": "Invalid file or file type not allowed"},
        413: {"description": "File size exceeds 20 MB limit"},
        422: {"description": "No file provided"},
        429: {"description": "Rate limit exceeded"}
    }
)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def upload_file(
    request: Request,
    file: UploadFile = File(..., description="File to upload (max 20 MB)"),
    session_id: Optional[str] = None,
    current_user: User = Depends(current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Upload a file securely to MinIO storage.
    
    **Request Body:**
    - **file**: File to upload (multipart/form-data)
    
    **Query Parameters:**
    - **session_id**: Optional session ID to link file to session
    
    **Response:**
    - File metadata with presigned URL for download
    
    **Security Features:**
    - File type validation (blocks dangerous executables)
    - Size limit enforcement (20 MB)
    - User ownership verification
    - Filename sanitization
    
    **Error Codes:**
    - **400**: Invalid file type
    - **413**: File too large
    - **422**: No file provided
    """
    
    # Validate file is provided
    if not file:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No file provided"
        )

    # Check content-length header first to prevent reading large files into memory
    content_length = request.headers.get('content-length')
    if content_length:
        content_size = int(content_length)
        if content_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds {MAX_FILE_SIZE // (1024*1024)} MB limit"
            )
    
    # Check file size from UploadFile if available
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {MAX_FILE_SIZE // (1024*1024)} MB limit"
        )
    
    # Validate file type
    content_type = file.content_type or "application/octet-stream"
    filename = file.filename or "uploaded_file"
    
    if not validate_file_type(content_type, filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed: {content_type}"
        )
    
    # Generate unique file ID
    file_id = str(uuid.uuid4())
    
    # Sanitize filename
    safe_filename = sanitize_filename(filename)
    
    # Create object key with session context
    if session_id:
        # Validate session exists and belongs to user
        try:
            session_object_id = ObjectId(session_id)
            session_doc = await db["sessions"].find_one({
                "_id": session_object_id,
                "user_id": ObjectId(current_user.id)
            })
            if not session_doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found or access denied"
                )
            object_key = f"{session_id}/{file_id}-{safe_filename}"
        except Exception as e:
            logger.warning(f"Invalid session_id {session_id}: {e}")
            object_key = f"user-{current_user.id}/{file_id}-{safe_filename}"
    else:
        object_key = f"user-{current_user.id}/{file_id}-{safe_filename}"
    
    try:
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Double-check size after reading
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds {MAX_FILE_SIZE // (1024*1024)} MB limit"
            )
        
        # Get MinIO client
        storage_client = get_minio_client()
        
        # Upload file using thread pool (MinIO SDK is blocking)
        from io import BytesIO
        file_stream = BytesIO(file_content)
        
        await run_in_threadpool(
            storage_client.upload_file,
            object_key,
            file_stream,
            file_size,
            content_type
        )
        
        # Generate presigned URL
        presigned_url = await run_in_threadpool(
            storage_client.get_presigned_url,
            object_key
        )
        
        # Create file metadata
        file_metadata = {
            "file_id": file_id,
            "object_key": object_key,
            "filename": filename,
            "safe_filename": safe_filename,
            "size": file_size,
            "content_type": content_type,
            "uploaded_by": ObjectId(current_user.id),
            "uploaded_at": datetime.now(timezone.utc),
            "session_id": ObjectId(session_id) if session_id else None
        }
        
        # Store file metadata in database (optional - for tracking)
        await db["files"].insert_one(file_metadata)
        
        # If session_id provided, link to session
        if session_id:
            await link_file_to_session(db, session_id, file_metadata)
        
        # Create response
        response = FileUploadResponse(
            file_id=file_id,
            url=presigned_url,
            size=file_size,
            mime=content_type
        )
        
        logger.info(f"✅ File uploaded: {file_id} ({file_size} bytes) for user {current_user.id}")
        
        return response.dict()
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except StorageError as e:
        # Handle storage-specific errors
        logger.error(f"Storage error uploading file: {e}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error uploading file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during file upload"
        )


async def link_file_to_session(
    db: AsyncIOMotorDatabase,
    session_id: str,
    file_metadata: Dict[str, Any]
) -> None:
    """
    Link uploaded file to session by updating contextSources
    
    Args:
        db: Database instance
        session_id: Session ObjectId string
        file_metadata: File metadata dictionary
    """
    try:
        session_object_id = ObjectId(session_id)
        
        # Create context source entry
        context_source = {
            "type": "file",
            "fileId": file_metadata["file_id"],
            "filename": file_metadata["filename"],
            "size": file_metadata["size"],
            "contentType": file_metadata["content_type"],
            "uploadedAt": file_metadata["uploaded_at"].isoformat()
        }
        
        # Update session to add context source
        result = await db["sessions"].update_one(
            {"_id": session_object_id},
            {
                "$push": {"settings.contextSources": context_source},
                "$set": {"updated_at": datetime.now(timezone.utc)}
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"✅ File {file_metadata['file_id']} linked to session {session_id}")
        else:
            logger.warning(f"⚠️  Failed to link file {file_metadata['file_id']} to session {session_id}")
            
    except Exception as e:
        logger.error(f"❌ Error linking file to session {session_id}: {e}")
        # Don't fail the upload if linking fails


@router.get(
    "/{file_id}",
    summary="Get file information",
    description="Get file metadata and download URL by file ID"
)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def get_file_info(
    request: Request,
    file_id: str,
    current_user: User = Depends(current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get file information and download URL.
    
    **Path Parameters:**
    - **file_id**: UUID of the uploaded file
    
    **Response:**
    - File metadata with fresh presigned URL
    
    **Error Codes:**
    - **404**: File not found or access denied
    - **500**: Storage service error
    """
    try:
        # Find file metadata
        file_doc = await db["files"].find_one({
            "file_id": file_id,
            "uploaded_by": ObjectId(current_user.id)
        })
        
        if not file_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found or access denied"
            )
        
        # Generate fresh presigned URL
        storage_client = get_minio_client()
        presigned_url = await run_in_threadpool(
            storage_client.get_presigned_url,
            file_doc["object_key"]
        )
        
        # Return file information
        return {
            "fileId": file_doc["file_id"],
            "filename": file_doc["filename"],
            "size": file_doc["size"],
            "contentType": file_doc["content_type"],
            "uploadedAt": file_doc["uploaded_at"].isoformat(),
            "url": presigned_url
        }
        
    except HTTPException:
        raise
    except StorageError as e:
        logger.error(f"Storage error getting file info: {e}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error getting file info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        ) 