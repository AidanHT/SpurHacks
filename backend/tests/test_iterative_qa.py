"""
Tests for Iterative Q&A Engine
Tests the complete Q&A loop functionality with mocked AI responses
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock
from bson import ObjectId

from backend.models.session import Session
from backend.models.node import Node
from backend.models.user import User
from backend.services.qa_loop import (
    get_session_with_validation,
    validate_node_ownership,
    check_stop_conditions,
    build_context_chain,
    truncate_context_for_tokens,
    parse_ai_response,
    insert_user_answer_node,
    insert_ai_node,
    update_session_status,
    QALoopError
)


@pytest.fixture
def mock_user():
    """Create a mock user for testing"""
    return User(
        id=str(ObjectId()),
        email="test@example.com",
        username="testuser",
        is_active=True,
        is_verified=True
    )


@pytest.fixture
def mock_session(mock_user):
    """Create a mock session for testing"""
    return Session(
        id=ObjectId(),
        user_id=ObjectId(mock_user.id),
        title="Test Session",
        starter_prompt="Help me write a creative story",
        max_questions=5,
        target_model="gpt-4",
        settings={"tone": "creative", "wordLimit": 500},
        status="active",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def mock_root_node(mock_session):
    """Create a mock root node for testing"""
    return Node(
        id=ObjectId(),
        session_id=mock_session.id,
        parent_id=None,
        role="user",
        content="I want to write a creative story",
        type="initial",
        created_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def mock_question_node(mock_session, mock_root_node):
    """Create a mock question node for testing"""
    return Node(
        id=ObjectId(),
        session_id=mock_session.id,
        parent_id=mock_root_node.id,
        role="assistant",
        content="Question: What genre would you like? Options: Fantasy, Sci-Fi, Mystery",
        type="question",
        created_at=datetime.now(timezone.utc)
    )


class TestQALoopHelpers:
    """Test the Q&A loop helper functions"""
    
    @pytest.mark.asyncio
    async def test_get_session_with_validation_success(self, mock_db, mock_session, mock_user):
        """Test successful session validation"""
        # Mock database response
        mock_db["sessions"].find_one = AsyncMock(return_value=mock_session.model_dump(by_alias=True))
        
        result = await get_session_with_validation(
            mock_db, mock_session.id, ObjectId(mock_user.id)
        )
        
        assert result.id == mock_session.id
        assert str(result.user_id) == mock_user.id
    
    @pytest.mark.asyncio
    async def test_get_session_with_validation_not_found(self, mock_db, mock_user):
        """Test session not found"""
        mock_db["sessions"].find_one = AsyncMock(return_value=None)
        
        with pytest.raises(QALoopError, match="Session not found"):
            await get_session_with_validation(
                mock_db, ObjectId(), ObjectId(mock_user.id)
            )
    
    @pytest.mark.asyncio
    async def test_get_session_with_validation_access_denied(self, mock_db, mock_session):
        """Test access denied for wrong user"""
        mock_db["sessions"].find_one = AsyncMock(return_value=mock_session.model_dump(by_alias=True))
        
        wrong_user_id = ObjectId()
        with pytest.raises(QALoopError, match="Access denied"):
            await get_session_with_validation(
                mock_db, mock_session.id, wrong_user_id
            )
    
    @pytest.mark.asyncio
    async def test_validate_node_ownership_success(self, mock_db, mock_question_node, mock_session):
        """Test successful node ownership validation"""
        mock_db["nodes"].find_one = AsyncMock(return_value=mock_question_node.model_dump(by_alias=True))
        
        result = await validate_node_ownership(
            mock_db, mock_question_node.id, mock_session.id
        )
        
        assert result.id == mock_question_node.id
        assert result.session_id == mock_session.id
    
    @pytest.mark.asyncio
    async def test_validate_node_ownership_not_found(self, mock_db, mock_session):
        """Test node not found"""
        mock_db["nodes"].find_one = AsyncMock(return_value=None)
        
        with pytest.raises(QALoopError, match="Node not found"):
            await validate_node_ownership(
                mock_db, ObjectId(), mock_session.id
            )
    
    @pytest.mark.asyncio
    async def test_check_stop_conditions_cancel_requested(self, mock_db, mock_session):
        """Test stop condition: cancel requested"""
        should_stop, reason = await check_stop_conditions(mock_db, mock_session, True)
        
        assert should_stop is True
        assert reason == "cancelled"
    
    @pytest.mark.asyncio
    async def test_check_stop_conditions_session_not_active(self, mock_db, mock_session):
        """Test stop condition: session not active"""
        mock_session.status = "completed"
        should_stop, reason = await check_stop_conditions(mock_db, mock_session, False)
        
        assert should_stop is True
        assert reason == "session_completed"
    
    @pytest.mark.asyncio
    async def test_check_stop_conditions_max_questions_reached(self, mock_db, mock_session):
        """Test stop condition: max questions reached"""
        mock_db["nodes"].count_documents = AsyncMock(return_value=5)
        
        should_stop, reason = await check_stop_conditions(mock_db, mock_session, False)
        
        assert should_stop is True
        assert reason == "max_questions_reached"
    
    @pytest.mark.asyncio
    async def test_check_stop_conditions_continue(self, mock_db, mock_session):
        """Test continue condition"""
        mock_db["nodes"].count_documents = AsyncMock(return_value=2)
        
        should_stop, reason = await check_stop_conditions(mock_db, mock_session, False)
        
        assert should_stop is False
        assert reason == ""
    
    def test_truncate_context_for_tokens_short_context(self):
        """Test context truncation with short context"""
        context_chain = [
            {"role": "user", "content": "Hello", "type": "initial", "created_at": datetime.now()},
            {"role": "assistant", "content": "Hi there!", "type": "question", "created_at": datetime.now()}
        ]
        
        result = truncate_context_for_tokens(context_chain, "Initial user prompt", 1000)
        
        assert "INITIAL USER CONTEXT" in result
        assert "Initial user prompt" in result
        assert "CONVERSATION HISTORY" in result
        assert "[user:initial] Hello" in result
        assert "[assistant:question] Hi there!" in result
    
    def test_truncate_context_for_tokens_long_context(self):
        """Test context truncation with long context"""
        long_content = "A" * 1000
        context_chain = [
            {"role": "user", "content": long_content, "type": "initial", "created_at": datetime.now()},
            {"role": "assistant", "content": "Short response", "type": "question", "created_at": datetime.now()}
        ]
        
        result = truncate_context_for_tokens(context_chain, "Initial context", 300)
        
        # Should include initial context and most recent conversation
        assert "INITIAL USER CONTEXT" in result
        assert "Initial context" in result
        assert len(result) <= 300
    
    @pytest.mark.asyncio
    async def test_parse_ai_response_question_format(self):
        """Test parsing AI response with question format"""
        raw_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": '{"question": "What genre?", "options": ["Fantasy", "Sci-Fi"], "selectionMethod": "single", "allowCustomAnswer": true}'
                            }
                        ]
                    }
                }
            ]
        }
        
        question, options, selection_method, allow_custom, final_prompt = await parse_ai_response(raw_response)
        
        assert question == "What genre?"
        assert options == ["Fantasy", "Sci-Fi"]
        assert selection_method == "single"
        assert allow_custom is True
        assert final_prompt is None
    
    @pytest.mark.asyncio
    async def test_parse_ai_response_final_prompt_format(self):
        """Test parsing AI response with final prompt format"""
        raw_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": '{"finalPrompt": "Write a fantasy story about dragons"}'
                            }
                        ]
                    }
                }
            ]
        }
        
        question, options, selection_method, allow_custom, final_prompt = await parse_ai_response(raw_response)
        
        assert question is None
        assert options is None
        assert selection_method is None
        assert allow_custom is None
        assert final_prompt == "Write a fantasy story about dragons"
    
    @pytest.mark.asyncio
    async def test_parse_ai_response_plain_text(self):
        """Test parsing AI response with plain text (treated as final prompt)"""
        raw_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": "Write a creative story about adventure"
                            }
                        ]
                    }
                }
            ]
        }
        
        question, options, selection_method, allow_custom, final_prompt = await parse_ai_response(raw_response)
        
        assert question is None
        assert options is None
        assert selection_method is None
        assert allow_custom is None
        assert final_prompt == "Write a creative story about adventure"
    
    @pytest.mark.asyncio
    async def test_parse_ai_response_with_custom_answer_allowed(self):
        """Test parsing AI response with custom answer functionality"""
        raw_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": '{"question": "What tone should your story have?", "options": ["Serious", "Humorous", "Mysterious", "Romantic"], "selectionMethod": "single", "allowCustomAnswer": true}'
                            }
                        ]
                    }
                }
            ]
        }
        
        question, options, selection_method, allow_custom, final_prompt = await parse_ai_response(raw_response)
        
        assert question == "What tone should your story have?"
        assert len(options) == 4
        assert "Serious" in options
        assert selection_method == "single"
        assert allow_custom is True
        assert final_prompt is None
    
    @pytest.mark.asyncio
    async def test_parse_ai_response_multi_selection(self):
        """Test parsing AI response with multi selection method"""
        raw_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": '{"question": "What features should be included?", "options": ["Authentication", "Database", "API", "Frontend"], "selectionMethod": "multi", "allowCustomAnswer": true}'
                            }
                        ]
                    }
                }
            ]
        }
        
        question, options, selection_method, allow_custom, final_prompt = await parse_ai_response(raw_response)
        
        assert question == "What features should be included?"
        assert len(options) == 4
        assert selection_method == "multi"
        assert allow_custom is True
        assert final_prompt is None
    
    @pytest.mark.asyncio
    async def test_parse_ai_response_ranking_selection(self):
        """Test parsing AI response with ranking selection method"""
        raw_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": '{"question": "Please rank these priorities in order:", "options": ["Performance", "Security", "Usability", "Cost"], "selectionMethod": "ranking", "allowCustomAnswer": true}'
                            }
                        ]
                    }
                }
            ]
        }
        
        question, options, selection_method, allow_custom, final_prompt = await parse_ai_response(raw_response)
        
        assert question == "Please rank these priorities in order:"
        assert len(options) == 4
        assert selection_method == "ranking"
        assert allow_custom is True
        assert final_prompt is None


class TestQALoopIntegration:
    """Integration tests for the complete Q&A loop"""
    
    @pytest.mark.asyncio
    async def test_complete_qa_loop_with_question_then_final(self, test_client, mock_user_token):
        """Test complete Q&A loop: question -> answer -> final prompt"""
        headers = {"Authorization": f"Bearer {mock_user_token}"}
        
        # 1. Create a session
        session_data = {
            "title": "Test Q&A Session",
            "starterPrompt": "Help me write a story",
            "maxQuestions": 5,
            "targetModel": "gpt-4",
            "settings": {"tone": "creative", "wordLimit": 500}
        }
        
        response = await test_client.post("/sessions", json=session_data, headers=headers)
        assert response.status_code == 201
        session = response.json()
        session_id = session["id"]
        
        # 2. Create initial node (simulate AI providing first question)
        # This would normally be done by the session creation flow
        # For testing, we'll insert a mock question node
        
        # Mock the first AI response to return a question
        mock_question_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": '{"question": "What genre would you like for your story?", "options": ["Fantasy", "Science Fiction", "Mystery", "Romance"]}'
                            }
                        ]
                    }
                }
            ]
        }
        
        # Mock the second AI response to return final prompt
        mock_final_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": '{"finalPrompt": "Write a fantasy story about a young wizard who discovers an ancient magical artifact that could save or destroy their world. The story should be creative and engaging, approximately 500 words."}'
                            }
                        ]
                    }
                }
            ]
        }
        
        # Create a mock root node to start the conversation
        from backend.core.database import get_database
        db = await get_database().__anext__()
        
        # Insert initial question node
        initial_node = Node(
            session_id=ObjectId(session_id),
            parent_id=None,
            role="assistant",
            content="What would you like to write about?",
            type="question",
            created_at=datetime.now(timezone.utc)
        )
        
        result = await db["nodes"].insert_one(initial_node.model_dump(by_alias=True))
        node_id = str(result.inserted_id)
        
        # 3. First answer - should get a question
        with patch('backend.services.ai_internal.ask_gemini', new_callable=AsyncMock) as mock_gemini:
            mock_gemini.return_value = mock_question_response
            
            answer_data = {
                "nodeId": node_id,
                "selected": ["Fantasy"]
            }
            
            response = await test_client.post(
                f"/sessions/{session_id}/answer",
                json=answer_data,
                headers=headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "question" in data
            assert "options" in data
            assert "selectionMethod" in data
            assert "allowCustomAnswer" in data
            assert "nodeId" in data
            assert data["question"] == "What genre would you like for your story?"
            assert "Fantasy" in data["options"]
            assert data["selectionMethod"] in ["single", "multi", "ranking"]
            assert isinstance(data["allowCustomAnswer"], bool)
            
            question_node_id = data["nodeId"]
        
        # 4. Second answer - should get final prompt
        with patch('backend.services.ai_internal.ask_gemini', new_callable=AsyncMock) as mock_gemini:
            mock_gemini.return_value = mock_final_response
            
            answer_data = {
                "nodeId": question_node_id,
                "selected": ["Fantasy"]
            }
            
            response = await test_client.post(
                f"/sessions/{session_id}/answer",
                json=answer_data,
                headers=headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "finalPrompt" in data
            assert "nodeId" in data
            assert "fantasy story" in data["finalPrompt"].lower()
            assert "wizard" in data["finalPrompt"].lower()
        
        # 5. Verify session is marked as completed
        response = await test_client.get(f"/sessions/{session_id}", headers=headers)
        assert response.status_code == 200
        session_data = response.json()
        assert session_data["status"] == "completed"
        
        # 6. Verify nodes were created correctly
        nodes = await db["nodes"].find({"session_id": ObjectId(session_id)}).to_list(length=None)
        
        # Should have: initial question + user answer + AI question + user answer + AI final
        assert len(nodes) == 5
        
        # Check node types
        node_types = [node["type"] for node in nodes if node.get("type")]
        assert "question" in node_types
        assert "answer" in node_types
        assert "final" in node_types
    
    @pytest.mark.asyncio
    async def test_qa_loop_max_questions_reached(self, test_client, mock_user_token):
        """Test Q&A loop stops when max questions reached"""
        headers = {"Authorization": f"Bearer {mock_user_token}"}
        
        # Create session with max 1 question
        session_data = {
            "title": "Limited Questions Session",
            "starterPrompt": "Help me write a story",
            "maxQuestions": 1,
            "targetModel": "gpt-4",
            "settings": {"tone": "creative", "wordLimit": 500}
        }
        
        response = await test_client.post("/sessions", json=session_data, headers=headers)
        assert response.status_code == 201
        session = response.json()
        session_id = session["id"]
        
        # Create initial question node and set up to reach max questions
        from backend.core.database import get_database
        db = await get_database().__anext__()
        
        # Insert initial question node
        initial_node = Node(
            session_id=ObjectId(session_id),
            parent_id=None,
            role="assistant",
            content="What would you like to write about?",
            type="question",
            created_at=datetime.now(timezone.utc)
        )
        
        result = await db["nodes"].insert_one(initial_node.model_dump(by_alias=True))
        node_id = str(result.inserted_id)
        
        # Answer the question - should trigger max questions reached
        answer_data = {
            "nodeId": node_id,
            "selected": ["Fantasy"]
        }
        
        response = await test_client.post(
            f"/sessions/{session_id}/answer",
            json=answer_data,
            headers=headers
        )
        
        assert response.status_code == 400
        assert "Maximum questions limit reached" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_qa_loop_cancel_session(self, test_client, mock_user_token):
        """Test Q&A loop cancellation"""
        headers = {"Authorization": f"Bearer {mock_user_token}"}
        
        # Create session
        session_data = {
            "title": "Cancellation Test Session",
            "starterPrompt": "Help me write a story",
            "maxQuestions": 5,
            "targetModel": "gpt-4",
            "settings": {"tone": "creative", "wordLimit": 500}
        }
        
        response = await test_client.post("/sessions", json=session_data, headers=headers)
        assert response.status_code == 201
        session = response.json()
        session_id = session["id"]
        
        # Create initial question node
        from backend.core.database import get_database
        db = await get_database().__anext__()
        
        initial_node = Node(
            session_id=ObjectId(session_id),
            parent_id=None,
            role="assistant",
            content="What would you like to write about?",
            type="question",
            created_at=datetime.now(timezone.utc)
        )
        
        result = await db["nodes"].insert_one(initial_node.model_dump(by_alias=True))
        node_id = str(result.inserted_id)
        
        # Answer with cancel flag
        answer_data = {
            "nodeId": node_id,
            "selected": ["Fantasy"],
            "cancel": True
        }
        
        response = await test_client.post(
            f"/sessions/{session_id}/answer",
            json=answer_data,
            headers=headers
        )
        
        assert response.status_code == 400
        assert "cancelled" in response.json()["detail"]
        
        # Verify session status
        response = await test_client.get(f"/sessions/{session_id}", headers=headers)
        assert response.status_code == 200
        session_data = response.json()
        assert session_data["status"] == "cancelled"
    
    @pytest.mark.asyncio
    async def test_qa_loop_invalid_node_id(self, test_client, mock_user_token):
        """Test Q&A loop with invalid node ID"""
        headers = {"Authorization": f"Bearer {mock_user_token}"}
        
        # Create session
        session_data = {
            "title": "Invalid Node Test",
            "starterPrompt": "Help me write a story",
            "maxQuestions": 5,
            "targetModel": "gpt-4",
            "settings": {"tone": "creative", "wordLimit": 500}
        }
        
        response = await test_client.post("/sessions", json=session_data, headers=headers)
        assert response.status_code == 201
        session = response.json()
        session_id = session["id"]
        
        # Try to answer with invalid node ID
        answer_data = {
            "nodeId": "invalid-node-id",
            "selected": ["Fantasy"]
        }
        
        response = await test_client.post(
            f"/sessions/{session_id}/answer",
            json=answer_data,
            headers=headers
        )
        
        assert response.status_code == 422
        assert "Invalid session or node ID format" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_qa_loop_node_not_in_session(self, test_client, mock_user_token):
        """Test Q&A loop with node that doesn't belong to session"""
        headers = {"Authorization": f"Bearer {mock_user_token}"}
        
        # Create session
        session_data = {
            "title": "Wrong Node Test",
            "starterPrompt": "Help me write a story",
            "maxQuestions": 5,
            "targetModel": "gpt-4",
            "settings": {"tone": "creative", "wordLimit": 500}
        }
        
        response = await test_client.post("/sessions", json=session_data, headers=headers)
        assert response.status_code == 201
        session = response.json()
        session_id = session["id"]
        
        # Create a node in a different session
        from backend.core.database import get_database
        db = await get_database().__anext__()
        
        wrong_node = Node(
            session_id=ObjectId(),  # Different session
            parent_id=None,
            role="assistant",
            content="Wrong session node",
            type="question",
            created_at=datetime.now(timezone.utc)
        )
        
        result = await db["nodes"].insert_one(wrong_node.model_dump(by_alias=True))
        wrong_node_id = str(result.inserted_id)
        
        # Try to answer with wrong node ID
        answer_data = {
            "nodeId": wrong_node_id,
            "selected": ["Fantasy"]
        }
        
        response = await test_client.post(
            f"/sessions/{session_id}/answer",
            json=answer_data,
            headers=headers
        )
        
        assert response.status_code == 404
        assert "Node does not belong to this session" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_qa_loop_with_custom_answer(self, test_client, mock_user_token):
        """Test Q&A loop with custom answer functionality"""
        headers = {"Authorization": f"Bearer {mock_user_token}"}
        
        # Create session
        session_data = {
            "title": "Custom Answer Test Session",
            "starterPrompt": "Help me write a story with specific requirements",
            "maxQuestions": 5,
            "targetModel": "gpt-4",
            "settings": {"tone": "creative", "wordLimit": 500}
        }
        
        response = await test_client.post("/sessions", json=session_data, headers=headers)
        assert response.status_code == 201
        session = response.json()
        session_id = session["id"]
        
        # Mock AI response that allows custom answers
        mock_custom_question_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": '{"question": "What unique setting would you like for your story?", "options": ["Medieval castle", "Space station", "Underwater city", "Floating islands"], "allowCustomAnswer": true}'
                            }
                        ]
                    }
                }
            ]
        }
        
        # Mock final response
        mock_final_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": '{"finalPrompt": "Write an engaging story set in a mystical forest inhabited by talking animals. The story should be creative and engaging, incorporating magical elements and a compelling narrative arc."}'
                            }
                        ]
                    }
                }
            ]
        }
        
        # Create initial question node
        from backend.core.database import get_database
        db = await get_database().__anext__()
        
        initial_node = Node(
            session_id=ObjectId(session_id),
            parent_id=None,
            role="assistant",
            content="What would you like to write about?",
            type="question",
            created_at=datetime.now(timezone.utc)
        )
        
        result = await db["nodes"].insert_one(initial_node.model_dump(by_alias=True))
        node_id = str(result.inserted_id)
        
        # First answer with custom response
        with patch('backend.services.ai_internal.ask_gemini', new_callable=AsyncMock) as mock_gemini:
            mock_gemini.return_value = mock_custom_question_response
            
            answer_data = {
                "nodeId": node_id,
                "selected": ["A mystical forest with talking animals"],
                "isCustomAnswer": True
            }
            
            response = await test_client.post(
                f"/sessions/{session_id}/answer",
                json=answer_data,
                headers=headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "question" in data
            assert "options" in data
            assert "selectionMethod" in data
            assert "allowCustomAnswer" in data
            assert data["allowCustomAnswer"] is True
            assert data["selectionMethod"] in ["single", "multi", "ranking"]
            assert "unique setting" in data["question"].lower()
            
            question_node_id = data["nodeId"]
        
        # Second answer (final)
        with patch('backend.services.ai_internal.ask_gemini', new_callable=AsyncMock) as mock_gemini:
            mock_gemini.return_value = mock_final_response
            
            answer_data = {
                "nodeId": question_node_id,
                "selected": ["Medieval castle"]
            }
            
            response = await test_client.post(
                f"/sessions/{session_id}/answer",
                json=answer_data,
                headers=headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "finalPrompt" in data
            assert "mystical forest" in data["finalPrompt"].lower()
        
        # Verify nodes include custom_answer type
        nodes = await db["nodes"].find({"session_id": ObjectId(session_id)}).to_list(length=None)
        
        # Find the custom answer node
        custom_answer_nodes = [node for node in nodes if node.get("type") == "custom_answer"]
        assert len(custom_answer_nodes) == 1
        assert "mystical forest" in custom_answer_nodes[0]["content"].lower()
    
    @pytest.mark.asyncio
    async def test_qa_loop_with_multi_select(self, test_client, mock_user_token):
        """Test Q&A loop with multi-select functionality"""
        headers = {"Authorization": f"Bearer {mock_user_token}"}
        
        # Create session
        session_data = {
            "title": "Multi-Select Test Session",
            "starterPrompt": "Help me build a web application",
            "maxQuestions": 5,
            "targetModel": "gpt-4",
            "settings": {"tone": "technical", "wordLimit": 1000}
        }
        
        response = await test_client.post("/sessions", json=session_data, headers=headers)
        assert response.status_code == 201
        session = response.json()
        session_id = session["id"]
        
        # Mock AI response with multi-select
        mock_multi_select_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": '{"question": "What features should your web application include?", "options": ["User Authentication", "Database Integration", "Real-time Chat", "Payment Processing", "File Upload"], "selectionMethod": "multi", "allowCustomAnswer": true}'
                            }
                        ]
                    }
                }
            ]
        }
        
        # Mock final response
        mock_final_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": '{"finalPrompt": "Create a comprehensive web application with user authentication and database integration. Include detailed implementation steps for secure user management and efficient data storage."}'
                            }
                        ]
                    }
                }
            ]
        }
        
        # Create initial question node
        from backend.core.database import get_database
        db = await get_database().__anext__()
        
        initial_node = Node(
            session_id=ObjectId(session_id),
            parent_id=None,
            role="assistant",
            content="What type of application do you want to build?",
            type="question",
            created_at=datetime.now(timezone.utc)
        )
        
        result = await db["nodes"].insert_one(initial_node.model_dump(by_alias=True))
        node_id = str(result.inserted_id)
        
        # Answer with multiple selections
        with patch('backend.services.ai_internal.ask_gemini', new_callable=AsyncMock) as mock_gemini:
            mock_gemini.return_value = mock_multi_select_response
            
            answer_data = {
                "nodeId": node_id,
                "selected": ["User Authentication", "Database Integration"]  # Multiple selections
            }
            
            response = await test_client.post(
                f"/sessions/{session_id}/answer",
                json=answer_data,
                headers=headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "question" in data
            assert "selectionMethod" in data
            assert data["selectionMethod"] == "multi"
            assert "features" in data["question"].lower()
            
            question_node_id = data["nodeId"]
        
        # Final answer
        with patch('backend.services.ai_internal.ask_gemini', new_callable=AsyncMock) as mock_gemini:
            mock_gemini.return_value = mock_final_response
            
            answer_data = {
                "nodeId": question_node_id,
                "selected": ["User Authentication", "Database Integration", "File Upload"]  # Multiple selections
            }
            
            response = await test_client.post(
                f"/sessions/{session_id}/answer",
                json=answer_data,
                headers=headers
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "finalPrompt" in data
            assert "authentication" in data["finalPrompt"].lower()
            assert "database" in data["finalPrompt"].lower()
        
        # Verify multi-select answers are properly stored
        nodes = await db["nodes"].find({"session_id": ObjectId(session_id)}).to_list(length=None)
        
        # Find answer nodes with multiple selections
        answer_nodes = [node for node in nodes if node.get("type") == "answer"]
        multi_select_answers = [node for node in answer_nodes if ";" in node["content"]]
        
        assert len(multi_select_answers) >= 1
        # Verify the format "Option1; Option2; Option3"
        assert "User Authentication; Database Integration" in multi_select_answers[0]["content"]