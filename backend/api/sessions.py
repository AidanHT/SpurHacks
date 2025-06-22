"""
Session API endpoints for Promptly
Handles session creation and retrieval with authentication
"""

import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from fastapi.responses import JSONResponse
from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field

from backend.auth import current_active_user
from backend.models.user import User
from backend.models.session import Session, SessionCreate, SessionRead
from backend.core.database import get_database
from backend.core.ratelimit import limiter, DEFAULT_RATE_LIMIT
from backend.services.qa_loop import (
    QALoopError,
    get_session_with_validation,
    validate_node_ownership,
    check_stop_conditions,
    build_context_chain,
    truncate_context_for_tokens,
    parse_ai_response,
    insert_user_answer_node,
    insert_ai_node,
    update_session_status
)
from backend.services.ai_internal import ask_gemini, GeminiServiceError

router = APIRouter(prefix="/sessions", tags=["sessions"])
logger = logging.getLogger(__name__)


class AnswerRequest(BaseModel):
    """Schema for answering a question in a session"""
    nodeId: str = Field(..., description="ObjectId of the node being answered")
    selected: List[str] = Field(..., min_items=1, description="User's selected answer(s) - single item for single/ranking, multiple for multi")
    isCustomAnswer: Optional[bool] = Field(False, description="Whether this is a custom user answer vs predefined option")
    cancel: Optional[bool] = Field(False, description="Whether to cancel the session")


class QuestionResponse(BaseModel):
    """Schema for AI question response"""
    question: str = Field(..., description="The AI-generated question")
    options: List[str] = Field(..., description="Available answer options (2-6 options)")
    selectionMethod: str = Field(..., description="Selection method: 'single', 'multi', or 'ranking'")
    allowCustomAnswer: bool = Field(default=True, description="Whether users can provide custom answers")
    nodeId: str = Field(..., description="ID of the created question node")


class FinalPromptResponse(BaseModel):
    """Schema for final prompt response"""
    finalPrompt: str = Field(..., description="The completed, refined prompt")
    nodeId: str = Field(..., description="ID of the created final node")


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
    db: AsyncIOMotorDatabase = Depends(get_database)
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
        status="active",
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


@router.post(
    "/{session_id}/answer",
    summary="Answer a question in the session",
    description="Submit an answer to continue the iterative Q&A loop"
)
@limiter.limit(DEFAULT_RATE_LIMIT)
async def answer_question(
    request: Request,
    session_id: str,
    answer_data: AnswerRequest,
    current_user: User = Depends(current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Submit an answer to continue the Q&A loop.
    
    **Path Parameters:**
    - **session_id**: MongoDB ObjectId of the session
    
    **Request Body:**
    - **nodeId**: ObjectId of the node being answered
    - **selected**: User's selected answer (1-5000 chars)
    - **cancel**: Optional flag to cancel the session
    
    **Response:**
    - **200**: Question or final prompt returned
    - **400**: Invalid request data
    - **401**: Authentication required
    - **403**: Access denied
    - **404**: Session or node not found
    - **422**: Invalid ID format
    - **429**: Rate limit exceeded
    - **502**: AI service error
    """
    start_time = time.time()
    
    # Validate ObjectId formats
    try:
        session_object_id = ObjectId(session_id)
        node_object_id = ObjectId(answer_data.nodeId)
    except InvalidId:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid session or node ID format"
        )
    
    try:
        # Start database transaction for consistency
        async with await db.client.start_session() as db_session:
            async with db_session.start_transaction():
                # 1. Validate session ownership
                try:
                    session = await get_session_with_validation(
                        db, session_object_id, ObjectId(current_user.id)
                    )
                except QALoopError as e:
                    if "not found" in str(e):
                        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
                    else:
                        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
                
                # 2. Validate node ownership
                try:
                    node = await validate_node_ownership(db, node_object_id, session_object_id)
                except QALoopError as e:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
                
                # 3. Check stop conditions
                should_stop, stop_reason = await check_stop_conditions(
                    db, session, answer_data.cancel
                )
                
                if should_stop:
                    # Update session status and commit before returning error
                    if stop_reason == "cancelled":
                        await update_session_status(db, db_session, session_object_id, "cancelled")
                        await db_session.commit_transaction()
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Session cancelled by user request"
                        )
                    elif stop_reason == "max_questions_reached":
                        await update_session_status(db, db_session, session_object_id, "completed")
                        await db_session.commit_transaction()
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Maximum questions limit reached"
                        )
                    else:
                        # For other stop reasons, don't update status but commit transaction
                        await db_session.commit_transaction()
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Session cannot continue: {stop_reason}"
                        )
                
                # 4. Insert user answer node
                answer_type = "custom_answer" if answer_data.isCustomAnswer else "answer"
                # Convert list to string for storage
                answer_content = "; ".join(answer_data.selected) if len(answer_data.selected) > 1 else answer_data.selected[0]
                user_node = await insert_user_answer_node(
                    db, db_session, session_object_id, node_object_id, answer_content, answer_type
                )
                
                # 5. Build context chain
                context_chain = await build_context_chain(db, session_object_id, user_node.id)
                context_string = truncate_context_for_tokens(context_chain, session.starter_prompt)
                
                # 6. Make AI call
                ai_payload = {
                    "prompt": f"""# AI Prompt Crafting Assistant

You are the foremost authority on prompt engineering. As the best prompt engineer in the world, you are helping users iteratively refine their prompts to achieve optimal results. Your goal is to transform their vague initial concept into a highly effective, laser-precise,well-structured prompt tailored specifically for their target AI model.

## Context Analysis
{context_string}

## Your Mission
Analyze the user's needs and conversation history above. You have two possible response modes:

### Mode 1: Ask a Clarifying Question
If you need more information to create the perfect prompt, ask **ONE strategic clarifying question** that will significantly improve the final result. Your question should:
- Target the most critical missing information
- Offer 2-6 specific, well-crafted options that cover different likely scenarios. Consider hundreds of possible options and choose the most relevant ones.
- Consider the target model's strengths and optimal input format
- Build upon previous conversation context
- Be concise and to the point

**Selection Methods Available:**
Choose the most appropriate method based on the nature of your question:

- **"single"**: User selects ONE option only. Use when options are mutually exclusive or contradictory
  - Examples: "What tone should your content have?" (Professional, Casual, Humorous)
  - Examples: "What's your primary goal?" (Educate, Entertain, Persuade)
  
- **"multi"**: User can select MULTIPLE options. Use when multiple elements can coexist and enhance the prompt
  - Examples: "What features should be included?" (Authentication, Database, API, Frontend)
  - Examples: "Which topics should be covered?" (Security, Performance, Scalability, Documentation)
  
- **"ranking"**: User ranks options by preference/priority. Use when order or priority matters for the final prompt
  - Examples: "Please rank these priorities in order:" (Speed, Accuracy, Cost-effectiveness, User Experience)
  - Examples: "Order these aspects by importance:" (Content Quality, SEO Optimization, Visual Appeal)

**Response Format for Questions:**
```json
{{
    "question": "What specific aspect would help craft the most effective prompt?",
    "options": ["Option 1", "Option 2", "Option 3", ...],
    "selectionMethod": "single",
    "allowCustomAnswer": true
}}
```

**Always set `"allowCustomAnswer": true`** as users can always provide their own input. The selection method applies to both predefined options AND any custom user input.

### Mode 2: Deliver the Final Prompt
If you have sufficient information, provide a complete, expertly-crafted prompt that:
- Is optimized specifically for **{session.target_model}**
- Incorporates all gathered context and preferences
- Follows best practices for the target model
- Includes clear instructions, format specifications, and examples where beneficial
- Addresses the user's core objective effectively

**Response Format for Final Prompt:**
```json
{{
    "finalPrompt": "Your expertly crafted, ready-to-use prompt here..."
}}
```

## Target Configuration
- **Model**: {session.target_model}
- **Settings**: {session.settings}
- **User Requirements**: Consider tone, length, style, and specific constraints mentioned

## Decision Criteria
Choose Mode 1 (question) if:
- Critical information is missing that would significantly improve the prompt
- The user's intent needs clarification
- Target model-specific optimizations require more details

Choose Mode 2 (final prompt) if:
- You have sufficient context to create an excellent prompt
- Further questions would provide diminishing returns
- The user has provided comprehensive guidance

Respond with **only** the JSON format - no additional text or explanations."""
                }
                
                try:
                    ai_start_time = time.time()
                    raw_response = await ask_gemini(ai_payload)
                    ai_elapsed = time.time() - ai_start_time
                    
                    logger.info(f"Gemini API call completed in {ai_elapsed:.2f}s")
                    
                except GeminiServiceError as e:
                    logger.error(f"Gemini service error: {e}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"AI service error: {e.detail}"
                    )
                
                # 7. Parse AI response
                question, options, selection_method, allow_custom_answer, final_prompt = await parse_ai_response(raw_response)
                
                if question and options:
                    # AI provided a question
                    custom_info = "\nAllows custom answer: Yes" if allow_custom_answer else "\nAllows custom answer: No"
                    selection_info = f"\nSelection method: {selection_method}"
                    question_content = f"Question: {question}\nOptions: {', '.join(options)}{selection_info}{custom_info}"
                    ai_node = await insert_ai_node(
                        db, db_session, session_object_id, user_node.id,
                        question_content, "question", raw_response
                    )
                    
                    elapsed_time = time.time() - start_time
                    logger.info(f"Q&A loop iteration completed in {elapsed_time:.2f}s")
                    
                    return QuestionResponse(
                        question=question,
                        options=options,
                        selectionMethod=selection_method or "single",
                        allowCustomAnswer=allow_custom_answer or True,
                        nodeId=str(ai_node.id)
                    )
                
                elif final_prompt:
                    # AI provided final prompt
                    ai_node = await insert_ai_node(
                        db, db_session, session_object_id, user_node.id,
                        final_prompt, "final", raw_response
                    )
                    
                    # Mark session as completed
                    await update_session_status(db, db_session, session_object_id, "completed")
                    
                    elapsed_time = time.time() - start_time
                    logger.info(f"Q&A loop completed with final prompt in {elapsed_time:.2f}s")
                    
                    return FinalPromptResponse(
                        finalPrompt=final_prompt,
                        nodeId=str(ai_node.id)
                    )
                
                else:
                    # Fallback - treat as final prompt
                    fallback_prompt = "Unable to generate a proper response. Please try again."
                    ai_node = await insert_ai_node(
                        db, db_session, session_object_id, user_node.id,
                        fallback_prompt, "final", raw_response
                    )
                    
                    await update_session_status(db, db_session, session_object_id, "completed")
                    
                    return FinalPromptResponse(
                        finalPrompt=fallback_prompt,
                        nodeId=str(ai_node.id)
                    )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in Q&A loop for session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during the Q&A loop"
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
    db: AsyncIOMotorDatabase = Depends(get_database)
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
    db: AsyncIOMotorDatabase = Depends(get_database),
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