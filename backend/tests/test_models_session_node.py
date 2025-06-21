"""
Tests for Session and Node models
Tests MongoDB operations, model validation, and index creation
"""

import os
import pytest
from datetime import datetime, timezone
from typing import AsyncGenerator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from bson import ObjectId

from backend.models import (
    Session, SessionCreate, SessionUpdate, SessionRead,
    Node, NodeCreate, NodeUpdate, NodeRead,
    PyObjectId, init_models
)


# Test database configuration
TEST_MONGODB_URL = os.getenv("MONGODB_URL_TEST", "mongodb://localhost:27017")
TEST_DATABASE_NAME = "test_promptly"


@pytest.fixture
async def test_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """
    Fixture providing a clean test database
    Creates connection, initializes indexes, and cleans up after tests
    """
    # Create test database connection
    client = AsyncIOMotorClient(TEST_MONGODB_URL, uuidRepresentation="standard")
    db = client[TEST_DATABASE_NAME]
    
    # Initialize indexes
    await init_models(db)
    
    yield db
    
    # Cleanup: drop test collections
    await db["sessions"].drop()
    await db["nodes"].drop()
    client.close()


@pytest.fixture
def sample_user_id() -> PyObjectId:
    """Fixture providing a sample user ObjectId for testing"""
    return PyObjectId()


class TestPyObjectId:
    """Test PyObjectId custom type"""
    
    def test_valid_object_id(self):
        """Test PyObjectId with valid ObjectId string"""
        valid_id = str(ObjectId())
        py_object_id = PyObjectId.validate(valid_id)
        assert isinstance(py_object_id, ObjectId)
        assert str(py_object_id) == valid_id
    
    def test_invalid_object_id(self):
        """Test PyObjectId with invalid ObjectId string"""
        with pytest.raises(ValueError, match="Invalid ObjectId"):
            PyObjectId.validate("invalid_id")
    
    def test_object_id_from_object_id(self):
        """Test PyObjectId with ObjectId instance"""
        original_id = ObjectId()
        py_object_id = PyObjectId.validate(original_id)
        assert py_object_id == original_id


class TestSession:
    """Test Session model"""
    
    def test_session_creation(self, sample_user_id):
        """Test creating a Session instance"""
        session = Session(
            user_id=sample_user_id,
            title="Test Session",
            metadata={"key": "value"}
        )
        
        assert isinstance(session.id, ObjectId)
        assert session.user_id == sample_user_id
        assert session.title == "Test Session"
        assert session.metadata == {"key": "value"}
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.updated_at, datetime)
    
    def test_session_defaults(self, sample_user_id):
        """Test Session with default values"""
        session = Session(user_id=sample_user_id)
        
        assert session.title is None
        assert session.metadata == {}
        assert session.created_at is not None
        assert session.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_session_crud_operations(self, test_db, sample_user_id):
        """Test Session CRUD operations in MongoDB"""
        collection = test_db["sessions"]
        
        # Create
        session = Session(
            user_id=sample_user_id,
            title="CRUD Test Session",
            metadata={"test": True}
        )
        result = await collection.insert_one(session.model_dump(by_alias=True))
        assert result.inserted_id == session.id
        
        # Read
        found_doc = await collection.find_one({"_id": session.id})
        assert found_doc is not None
        found_session = Session(**found_doc)
        assert found_session.title == "CRUD Test Session"
        assert found_session.user_id == sample_user_id
        
        # Update
        update_data = SessionUpdate(
            title="Updated Title",
            metadata={"updated": True}
        )
        await collection.update_one(
            {"_id": session.id},
            {"$set": update_data.model_dump(exclude_unset=True)}
        )
        
        updated_doc = await collection.find_one({"_id": session.id})
        updated_session = Session(**updated_doc)
        assert updated_session.title == "Updated Title"
        assert updated_session.metadata == {"updated": True}
        
        # Delete
        await collection.delete_one({"_id": session.id})
        deleted_doc = await collection.find_one({"_id": session.id})
        assert deleted_doc is None
    
    @pytest.mark.asyncio
    async def test_session_indexes(self, test_db, sample_user_id):
        """Test that Session indexes work correctly"""
        collection = test_db["sessions"]
        
        # Insert multiple sessions
        sessions = []
        for i in range(3):
            session = Session(
                user_id=sample_user_id,
                title=f"Session {i}"
            )
            await collection.insert_one(session.model_dump(by_alias=True))
            sessions.append(session)
        
        # Test user_sessions_by_time index (latest first)
        cursor = collection.find({"user_id": sample_user_id}).sort([
            ("user_id", 1),
            ("created_at", -1)
        ])
        results = await cursor.to_list(length=None)
        assert len(results) == 3
        
        # Verify index exists
        indexes = await collection.index_information()
        assert "user_sessions_by_time" in indexes


class TestNode:
    """Test Node model"""
    
    def test_node_creation(self, sample_user_id):
        """Test creating a Node instance"""
        session_id = PyObjectId()
        parent_id = PyObjectId()
        
        node = Node(
            session_id=session_id,
            parent_id=parent_id,
            role="question",
            content="What is your goal?"
        )
        
        assert isinstance(node.id, ObjectId)
        assert node.session_id == session_id
        assert node.parent_id == parent_id
        assert node.role == "question"
        assert node.content == "What is your goal?"
        assert isinstance(node.created_at, datetime)
    
    def test_node_without_parent(self):
        """Test Node without parent (root node)"""
        session_id = PyObjectId()
        
        node = Node(
            session_id=session_id,
            role="prompt",
            content="Initial prompt"
        )
        
        assert node.parent_id is None
        assert node.session_id == session_id
    
    @pytest.mark.asyncio
    async def test_node_crud_operations(self, test_db, sample_user_id):
        """Test Node CRUD operations in MongoDB"""
        # First create a session
        session_collection = test_db["sessions"]
        session = Session(user_id=sample_user_id, title="Test Session")
        await session_collection.insert_one(session.model_dump(by_alias=True))
        
        # Now test Node operations
        node_collection = test_db["nodes"]
        
        # Create root node
        root_node = Node(
            session_id=session.id,
            role="prompt",
            content="Root prompt"
        )
        result = await node_collection.insert_one(root_node.model_dump(by_alias=True))
        assert result.inserted_id == root_node.id
        
        # Create child node
        child_node = Node(
            session_id=session.id,
            parent_id=root_node.id,
            role="question",
            content="Follow-up question"
        )
        await node_collection.insert_one(child_node.dict(by_alias=True))
        
        # Read nodes by session
        cursor = node_collection.find({"session_id": session.id})
        nodes = await cursor.to_list(length=None)
        assert len(nodes) == 2
        
        # Read child nodes by parent
        cursor = node_collection.find({"parent_id": root_node.id})
        children = await cursor.to_list(length=None)
        assert len(children) == 1
        assert children[0]["content"] == "Follow-up question"
    
    @pytest.mark.asyncio
    async def test_node_indexes(self, test_db, sample_user_id):
        """Test that Node indexes work correctly"""
        # Create test session
        session_collection = test_db["sessions"]
        session = Session(user_id=sample_user_id)
        await session_collection.insert_one(session.dict(by_alias=True))
        
        node_collection = test_db["nodes"]
        
        # Create test nodes
        root_node = Node(
            session_id=session.id,
            role="prompt",
            content="Root"
        )
        await node_collection.insert_one(root_node.model_dump(by_alias=True))
        
        child_node = Node(
            session_id=session.id,
            parent_id=root_node.id,
            role="answer",
            content="Child"
        )
        await node_collection.insert_one(child_node.dict(by_alias=True))
        
        # Test session_parent_nodes index
        cursor = node_collection.find({
            "session_id": session.id,
            "parent_id": root_node.id
        })
        results = await cursor.to_list(length=None)
        assert len(results) == 1
        
        # Verify indexes exist
        indexes = await node_collection.index_information()
        assert "session_parent_nodes" in indexes
        assert "session_nodes_by_time" in indexes


class TestModelIntegration:
    """Test Session and Node integration"""
    
    @pytest.mark.asyncio
    async def test_session_with_nodes(self, test_db, sample_user_id):
        """Test creating a session with multiple nodes forming a tree"""
        # Create session
        session_collection = test_db["sessions"]
        session = Session(
            user_id=sample_user_id,
            title="Integration Test Session"
        )
        await session_collection.insert_one(session.dict(by_alias=True))
        
        # Create node tree
        node_collection = test_db["nodes"]
        
        # Root node
        root = Node(
            session_id=session.id,
            role="prompt",
            content="What kind of content do you want to create?"
        )
        await node_collection.insert_one(root.dict(by_alias=True))
        
        # First level children
        child1 = Node(
            session_id=session.id,
            parent_id=root.id,
            role="answer",
            content="Blog post"
        )
        child2 = Node(
            session_id=session.id,
            parent_id=root.id,
            role="answer", 
            content="Technical documentation"
        )
        
        await node_collection.insert_many([
            child1.dict(by_alias=True),
            child2.dict(by_alias=True)
        ])
        
        # Second level child
        grandchild = Node(
            session_id=session.id,
            parent_id=child1.id,
            role="question",
            content="What topic should the blog post cover?"
        )
        await node_collection.insert_one(grandchild.dict(by_alias=True))
        
        # Verify the tree structure
        # Root should have 2 children
        root_children = await node_collection.find({"parent_id": root.id}).to_list(length=None)
        assert len(root_children) == 2
        
        # child1 should have 1 child
        child1_children = await node_collection.find({"parent_id": child1.id}).to_list(length=None)
        assert len(child1_children) == 1
        
        # child2 should have no children
        child2_children = await node_collection.find({"parent_id": child2.id}).to_list(length=None)
        assert len(child2_children) == 0
        
        # Total nodes in session should be 4
        total_nodes = await node_collection.count_documents({"session_id": session.id})
        assert total_nodes == 4
    
    @pytest.mark.asyncio
    async def test_foreign_key_validation(self, test_db, sample_user_id):
        """Test that foreign key relationships are maintained"""
        session_collection = test_db["sessions"]
        node_collection = test_db["nodes"]
        
        # Create session
        session = Session(user_id=sample_user_id)
        await session_collection.insert_one(session.dict(by_alias=True))
        
        # Create node with valid session_id
        node = Node(
            session_id=session.id,
            role="prompt",
            content="Valid node"
        )
        result = await node_collection.insert_one(node.dict(by_alias=True))
        assert result.inserted_id is not None
        
        # Verify node exists in session
        node_count = await node_collection.count_documents({"session_id": session.id})
        assert node_count == 1
        
        # Create node with non-existent parent_id (should still work in MongoDB)
        # Note: MongoDB doesn't enforce foreign key constraints
        fake_parent_id = PyObjectId()
        orphan_node = Node(
            session_id=session.id,
            parent_id=fake_parent_id,
            role="orphan",
            content="Orphan node"
        )
        result = await node_collection.insert_one(orphan_node.dict(by_alias=True))
        assert result.inserted_id is not None  # MongoDB allows this
        
        # Application logic should handle foreign key validation 