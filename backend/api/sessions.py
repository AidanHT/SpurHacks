"""
Session API endpoints for Promptly
Handles session creation and retrieval with authentication
"""

from datetime import datetime, timezone
from typing import Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from fastapi.responses import JSONResponse
from bson import ObjectId
from bson.errors import InvalidId

from backend.auth import current_active_user
from backend.models.user import User
from backend.models.session import Session, SessionCreate, SessionRead
from backend.core.database import get_database
from backend.core.ratelimit import limiter, DEFAULT_RATE_LIMIT

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post(
    "",
    response_model=SessionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new session",
    description="Create a new AI prompt crafting session for the authenticated user"
)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def create_session(
    request: Request,
    session_data: SessionCreate,
    current_user: User = Depends(current_active_user),
    db = Depends(get_database)
):
    """
    Create a new session for the authenticated user.
    
    **Request Body:**
    - **starterPrompt**: Initial prompt text (1-5000 chars)
    - **maxQuestions**: Maximum questions allowed (1-20)
    - **targetModel**: AI model to use (must be supported)
    - **settings**: Configuration object with tone and wordLimit
    - **title**: Optional session title (max 200 chars)
    - **metadata**: Optional additional metadata
    
    **Response:**
    - **201**: Session created successfully
    - **400**: Invalid request data
    - **401**: Authentication required
    - **422**: Validation error
    - **429**: Rate limit exceeded
    """
    # Create session document
    session = Session(
        user_id=ObjectId(current_user.id),
        title=session_data.title,
        metadata=session_data.metadata or {},
        starter_prompt=session_data.starter_prompt,
        max_questions=session_data.max_questions,
        target_model=session_data.target_model,
        settings=session_data.settings,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    # Insert into database
    collection = db["sessions"]
    try:
        result = await collection.insert_one(session.model_dump(by_alias=True))
        
        # Retrieve the created session
        created_session = await collection.find_one({"_id": result.inserted_id})
        if not created_session:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created session"
            )
        
        # Convert to response model
        session_response = SessionRead(**created_session)
        
        # Create response with Location header
        response = JSONResponse(
            content=session_response.model_dump(),
            status_code=status.HTTP_201_CREATED
        )
        response.headers["Location"] = f"/sessions/{session_response.id}"
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except ValueError as e:
        # Handle validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid session data: {str(e)}"
        )
    except Exception as e:
        # Handle unexpected database errors
        import logging
        logging.error(f"Unexpected error creating session for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the session"
        )


@router.get(
    "/{session_id}",
    response_model=SessionRead,
    summary="Get session by ID",
    description="Retrieve a specific session by its ID (only accessible by owner)"
)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def get_session(
    request: Request,
    session_id: str,
    current_user: User = Depends(current_active_user),
    db = Depends(get_database)
):
    """
    Retrieve a session by its ID.
    
    **Path Parameters:**
    - **session_id**: MongoDB ObjectId of the session
    
    **Response:**
    - **200**: Session retrieved successfully
    - **401**: Authentication required
    - **403**: Access denied (not session owner)
    - **404**: Session not found
    - **422**: Invalid session ID format
    - **429**: Rate limit exceeded
    """
    # Validate ObjectId format
    try:
        session_object_id = ObjectId(session_id)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid session ID format"
        )
    
    # Find session in database
    collection = db["sessions"]
    session_doc = await collection.find_one({"_id": session_object_id})
    
    if not session_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Check ownership
    session = Session(**session_doc)
    if str(session.user_id) != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You can only access your own sessions"
        )
    
    # Return session data
    return SessionRead(**session_doc)


@router.get(
    "",
    response_model=List[SessionRead],
    summary="List user sessions",
    description="Get all sessions for the authenticated user, ordered by creation time (latest first)"
)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def list_sessions(
    request: Request,
    current_user: User = Depends(current_active_user),
    db = Depends(get_database),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of sessions to return"),
    skip: int = Query(default=0, ge=0, description="Number of sessions to skip for pagination")
):
    """
    List all sessions for the authenticated user.
    
    **Query Parameters:**
    - **limit**: Maximum number of sessions to return (default: 50, max: 100)
    - **skip**: Number of sessions to skip for pagination (default: 0)
    
    **Response:**
    - **200**: Sessions retrieved successfully
    - **401**: Authentication required
    - **422**: Invalid pagination parameters
    - **429**: Rate limit exceeded
    """
    # No need for manual validation - FastAPI handles it with Query validation
    
    # Query user sessions
    collection = db["sessions"]
    cursor = collection.find(
        {"user_id": ObjectId(current_user.id)}
    ).sort([
        ("created_at", -1)  # Latest first
    ]).skip(skip).limit(limit)
    
    sessions = await cursor.to_list(length=None)
    
    # Convert to response models
    return [SessionRead(**session) for session in sessions] 