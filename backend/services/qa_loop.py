"""
Q&A Loop Service for Promptly
Handles iterative question-answer dialogue logic
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorClientSession

from backend.models.session import Session
from backend.models.node import Node
from backend.services.ai_internal import ask_gemini, GeminiServiceError

logger = logging.getLogger(__name__)


class QALoopError(Exception):
    """Custom exception for Q&A loop errors"""
    pass


async def get_session_with_validation(
    db: AsyncIOMotorDatabase,
    session_id: ObjectId,
    user_id: ObjectId
) -> Session:
    """
    Get session and validate ownership
    
    Args:
        db: Database instance
        session_id: Session ObjectId
        user_id: User ObjectId
        
    Returns:
        Session object
        
    Raises:
        QALoopError: If session not found or access denied
    """
    collection = db["sessions"]
    session_doc = await collection.find_one({"_id": session_id})
    
    if not session_doc:
        raise QALoopError("Session not found")
    
    session = Session(**session_doc)
    
    if str(session.user_id) != str(user_id):
        raise QALoopError("Access denied: You can only access your own sessions")
    
    return session


async def validate_node_ownership(
    db: AsyncIOMotorDatabase,
    node_id: ObjectId,
    session_id: ObjectId
) -> Node:
    """
    Validate that node belongs to the session
    
    Args:
        db: Database instance
        node_id: Node ObjectId
        session_id: Session ObjectId
        
    Returns:
        Node object
        
    Raises:
        QALoopError: If node not found or doesn't belong to session
    """
    collection = db["nodes"]
    node_doc = await collection.find_one({"_id": node_id})
    
    if not node_doc:
        raise QALoopError("Node not found")
    
    node = Node(**node_doc)
    
    if str(node.session_id) != str(session_id):
        raise QALoopError("Node does not belong to this session")
    
    return node


async def check_stop_conditions(
    db: AsyncIOMotorDatabase,
    session: Session,
    cancel_requested: bool = False
) -> Tuple[bool, str]:
    """
    Check if the Q&A loop should stop
    
    Args:
        db: Database instance
        session: Session object
        cancel_requested: Whether user requested cancellation
        
    Returns:
        Tuple of (should_stop, reason)
    """
    if cancel_requested:
        return True, "cancelled"
    
    if session.status != "active":
        return True, f"session_{session.status}"
    
    # Count AI questions in this session
    collection = db["nodes"]
    question_count = await collection.count_documents({
        "session_id": session.id,
        "role": "assistant",
        "type": "question"
    })
    
    if question_count >= session.max_questions:
        return True, "max_questions_reached"
    
    return False, ""


async def build_context_chain(
    db: AsyncIOMotorDatabase,
    session_id: ObjectId,
    node_id: ObjectId
) -> List[Dict[str, Any]]:
    """
    Build the full context chain from root to the specified node
    
    Args:
        db: Database instance
        session_id: Session ObjectId
        node_id: Starting node ObjectId
        
    Returns:
        List of context entries ordered by creation time
    """
    collection = db["nodes"]
    
    # Get all nodes in the session
    cursor = collection.find(
        {"session_id": session_id}
    ).sort("created_at", 1)
    
    nodes = await cursor.to_list(length=None)
    
    if not nodes:
        return []
    
    # Build a map of nodes by ID for efficient lookup
    node_map = {str(node["_id"]): node for node in nodes}
    
    # Find the path from root to target node
    context_chain = []
    current_node_id = str(node_id)
    
    # Build the chain by walking up the parent hierarchy
    visited = set()
    while current_node_id and current_node_id in node_map:
        if current_node_id in visited:
            # Prevent infinite loops
            logger.warning(f"Circular reference detected in node chain: {current_node_id}")
            break
        
        visited.add(current_node_id)
        node = node_map[current_node_id]
        
        context_chain.append({
            "role": node["role"],
            "content": node["content"],
            "type": node.get("type"),
            "created_at": node["created_at"]
        })
        
        # Move to parent
        current_node_id = str(node["parent_id"]) if node.get("parent_id") else None
    
    # Reverse to get root-to-leaf order
    context_chain.reverse()
    
    return context_chain


def truncate_context_for_tokens(context_chain: List[Dict[str, Any]], max_chars: int = 2000) -> str:
    """
    Build context string and truncate if needed to stay within token limits
    
    Args:
        context_chain: List of context entries
        max_chars: Maximum characters allowed (default: 2000)
        
    Returns:
        Formatted context string
    """
    if not context_chain:
        return ""
    
    # Build the full context
    context_parts = []
    for entry in context_chain:
        role = entry["role"]
        content = entry["content"]
        entry_type = entry.get("type", "")
        
        if entry_type:
            context_parts.append(f"[{role}:{entry_type}] {content}")
        else:
            context_parts.append(f"[{role}] {content}")
    
    full_context = "\n\n".join(context_parts)
    
    # Truncate if too long, keeping the most recent entries
    if len(full_context) <= max_chars:
        return full_context
    
    # Try to fit as many recent entries as possible
    truncated_parts = []
    current_length = 0
    
    for entry in reversed(context_chain):
        role = entry["role"]
        content = entry["content"]
        entry_type = entry.get("type", "")
        
        if entry_type:
            entry_text = f"[{role}:{entry_type}] {content}"
        else:
            entry_text = f"[{role}] {content}"
        
        if current_length + len(entry_text) + 2 > max_chars:  # +2 for \n\n
            break
        
        truncated_parts.append(entry_text)
        current_length += len(entry_text) + 2
    
    if not truncated_parts:
        # If even the last entry is too long, truncate it
        last_entry = context_chain[-1]
        role = last_entry["role"]
        content = last_entry["content"]
        entry_type = last_entry.get("type", "")
        
        prefix = f"[{role}:{entry_type}] " if entry_type else f"[{role}] "
        available_chars = max_chars - len(prefix) - 12  # 12 for "…[truncated]"
        
        if available_chars > 0:
            truncated_content = content[:available_chars] + "…[truncated]"
            return f"{prefix}{truncated_content}"
        else:
            return f"{prefix}…[truncated]"
    
    # Reverse back to chronological order
    truncated_parts.reverse()
    return "\n\n".join(truncated_parts)


async def parse_ai_response(raw_response: Dict[str, Any]) -> Tuple[Optional[str], Optional[List[str]], Optional[str]]:
    """
    Parse AI response to extract question, options, or final prompt
    
    Args:
        raw_response: Raw response from Gemini API
        
    Returns:
        Tuple of (question, options, final_prompt)
    """
    try:
        # Extract text from Gemini response format
        candidates = raw_response.get("candidates", [])
        if not candidates:
            return None, None, "No response generated"
        
        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        if not parts:
            return None, None, "No content in response"
        
        text = parts[0].get("text", "").strip()
        if not text:
            return None, None, "Empty response"
        
        # Try to parse as JSON first
        try:
            parsed = json.loads(text)
            
            # Check for question format
            if "question" in parsed and "options" in parsed:
                question = parsed["question"]
                options = parsed["options"]
                
                if isinstance(question, str) and isinstance(options, list):
                    return question, options, None
            
            # Check for final prompt format
            if "finalPrompt" in parsed:
                final_prompt = parsed["finalPrompt"]
                if isinstance(final_prompt, str):
                    return None, None, final_prompt
                    
        except json.JSONDecodeError:
            # Not JSON, treat as final prompt
            pass
        
        # Default: treat as final prompt
        return None, None, text
        
    except Exception as e:
        logger.error(f"Error parsing AI response: {e}")
        return None, None, f"Error parsing response: {str(e)}"


async def insert_user_answer_node(
    db: AsyncIOMotorDatabase,
    session: AsyncIOMotorClientSession,
    session_id: ObjectId,
    parent_id: ObjectId,
    answer: str
) -> Node:
    """
    Insert user answer node
    
    Args:
        db: Database instance
        session: Database session for transactions
        session_id: Session ObjectId
        parent_id: Parent node ObjectId
        answer: User's answer text
        
    Returns:
        Created Node object
    """
    node = Node(
        session_id=session_id,
        parent_id=parent_id,
        role="user",
        content=answer,
        type="answer",
        created_at=datetime.now(timezone.utc)
    )
    
    collection = db["nodes"]
    result = await collection.insert_one(
        node.model_dump(by_alias=True),
        session=session
    )
    
    node.id = result.inserted_id
    return node


async def insert_ai_node(
    db: AsyncIOMotorDatabase,
    session: AsyncIOMotorClientSession,
    session_id: ObjectId,
    parent_id: ObjectId,
    content: str,
    node_type: str,
    raw_response: Dict[str, Any]
) -> Node:
    """
    Insert AI response node
    
    Args:
        db: Database instance
        session: Database session for transactions
        session_id: Session ObjectId
        parent_id: Parent node ObjectId
        content: AI response content
        node_type: Node type ("question" or "final")
        raw_response: Raw AI response for debugging
        
    Returns:
        Created Node object
    """
    node = Node(
        session_id=session_id,
        parent_id=parent_id,
        role="assistant",
        content=content,
        type=node_type,
        extra={"raw": raw_response},
        created_at=datetime.now(timezone.utc)
    )
    
    collection = db["nodes"]
    result = await collection.insert_one(
        node.model_dump(by_alias=True),
        session=session
    )
    
    node.id = result.inserted_id
    return node


async def update_session_status(
    db: AsyncIOMotorDatabase,
    session: AsyncIOMotorClientSession,
    session_id: ObjectId,
    status: str
) -> None:
    """
    Update session status
    
    Args:
        db: Database instance
        session: Database session for transactions
        session_id: Session ObjectId
        status: New status
    """
    collection = db["sessions"]
    await collection.update_one(
        {"_id": session_id},
        {
            "$set": {
                "status": status,
                "updated_at": datetime.now(timezone.utc)
            }
        },
        session=session
    ) 