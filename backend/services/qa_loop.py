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

from models.session import Session
from models.node import Node
from services.ai_internal import ask_gemini, GeminiServiceError

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
        List of context entries ordered chronologically (root to leaf)
        representing the conversation path leading to the specified node
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
    # Ensure consistent ObjectId string conversion
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


def truncate_context_for_tokens(
    context_chain: List[Dict[str, Any]], 
    starter_prompt: str = "", 
    max_chars: int = 2000
) -> str:
    """
    Build context string with initial context and truncate if needed to stay within token limits
    
    Args:
        context_chain: List of context entries
        starter_prompt: Initial user context/prompt to include
        max_chars: Maximum characters allowed (default: 2000)
        
    Returns:
        Formatted context string with initial context section
    """
    # Start with initial context section if provided
    context_sections = []
    
    if starter_prompt and starter_prompt.strip():
        initial_section = f"=== INITIAL USER CONTEXT ===\n{starter_prompt.strip()}\n"
        context_sections.append(initial_section)
    
    # Add conversation history section if we have entries
    if context_chain:
        conversation_parts = []
        for entry in context_chain:
            role = entry["role"]
            content = entry["content"]
            entry_type = entry.get("type", "")
            
            if entry_type:
                conversation_parts.append(f"[{role}:{entry_type}] {content}")
            else:
                conversation_parts.append(f"[{role}] {content}")
        
        if conversation_parts:
            conversation_section = "=== CONVERSATION HISTORY ===\n" + "\n\n".join(conversation_parts)
            context_sections.append(conversation_section)
    
    if not context_sections:
        return ""
    
    full_context = "\n\n".join(context_sections)
    
    # If within limits, return full context
    if len(full_context) <= max_chars:
        return full_context
    
    # Need to truncate - prioritize initial context, then recent conversation
    reserved_for_initial = min(len(context_sections[0]) if context_sections else 0, max_chars // 3)
    available_for_conversation = max_chars - reserved_for_initial - 50  # Reserve space for separators
    
    # Always include initial context if present
    truncated_sections = []
    if starter_prompt and starter_prompt.strip():
        if len(context_sections[0]) <= reserved_for_initial:
            truncated_sections.append(context_sections[0])
        else:
            # Truncate initial context if too long
            truncated_initial = context_sections[0][:reserved_for_initial - 15] + "…[truncated]\n"
            truncated_sections.append(truncated_initial)
    
    # Try to fit recent conversation entries
    if context_chain and available_for_conversation > 100:
        conversation_parts = []
        current_length = 0
        header_text = "=== CONVERSATION HISTORY ===\n"
        
        for entry in reversed(context_chain):
            role = entry["role"]
            content = entry["content"]
            entry_type = entry.get("type", "")
            
            if entry_type:
                entry_text = f"[{role}:{entry_type}] {content}"
            else:
                entry_text = f"[{role}] {content}"
            
            if current_length + len(entry_text) + 2 > available_for_conversation - len(header_text):
                break
            
            conversation_parts.append(entry_text)
            current_length += len(entry_text) + 2
        
        if conversation_parts:
            conversation_parts.reverse()  # Back to chronological order
            conversation_section = header_text + "\n\n".join(conversation_parts)
            truncated_sections.append(conversation_section)
    
    return "\n\n".join(truncated_sections) if truncated_sections else "…[truncated]"


async def parse_ai_response(raw_response: Dict[str, Any]) -> Tuple[Optional[str], Optional[List[str]], Optional[str], Optional[bool], Optional[str]]:
    """
    Parse AI response to extract question, options, selection method, custom answer flag, or final prompt
    
    Args:
        raw_response: Raw response from Gemini API
        
    Returns:
        Tuple of (question, options, selection_method, allow_custom_answer, final_prompt)
    """
    try:
        # Extract text from Gemini response format
        candidates = raw_response.get("candidates", [])
        if not candidates:
            return None, None, None, None, "No response generated"
        
        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        if not parts:
            return None, None, None, None, "No content in response"
        
        text = parts[0].get("text", "").strip()
        if not text:
            return None, None, None, None, "Empty response"
        
        # Try to parse as JSON first
        try:
            parsed = json.loads(text)
            
            # Check for question format
            if "question" in parsed and "options" in parsed:
                question = parsed["question"]
                options = parsed["options"]
                selection_method = parsed.get("selectionMethod", "single")
                allow_custom = parsed.get("allowCustomAnswer", True)  # Default to True now
                
                if isinstance(question, str) and isinstance(options, list):
                    # Validate options length (2-6 as requested)
                    if len(options) < 2 or len(options) > 6:
                        logger.warning(f"AI provided {len(options)} options, expected 2-6. Truncating/padding.")
                        if len(options) > 6:
                            options = options[:6]
                        elif len(options) < 2:
                            options.extend(["Other", "Not sure"][:2 - len(options)])
                    
                    # Validate selection method
                    valid_methods = ["single", "multi", "ranking"]
                    if selection_method not in valid_methods:
                        logger.warning(f"AI provided invalid selection method '{selection_method}', defaulting to 'single'")
                        selection_method = "single"
                    
                    return question, options, selection_method, allow_custom, None
            
            # Check for final prompt format
            if "finalPrompt" in parsed:
                final_prompt = parsed["finalPrompt"]
                if isinstance(final_prompt, str):
                    return None, None, None, None, final_prompt
                    
        except json.JSONDecodeError:
            # Not JSON, treat as final prompt
            pass
        
        # Default: treat as final prompt
        return None, None, None, None, text
        
    except Exception as e:
        logger.error(f"Error parsing AI response: {e}")
        return None, None, None, None, f"Error parsing response: {str(e)}"


async def insert_user_answer_node(
    db: AsyncIOMotorDatabase,
    session: AsyncIOMotorClientSession,
    session_id: ObjectId,
    parent_id: ObjectId,
    answer: str,
    answer_type: str = "answer"
) -> Node:
    """
    Insert user answer node
    
    Args:
        db: Database instance
        session: Database session for transactions
        session_id: Session ObjectId
        parent_id: Parent node ObjectId
        answer: User's answer text
        answer_type: Type of answer ("answer" or "custom_answer")
        
    Returns:
        Created Node object
    """
    node = Node(
        session_id=session_id,
        parent_id=parent_id,
        role="user",
        content=answer,
        type=answer_type,
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