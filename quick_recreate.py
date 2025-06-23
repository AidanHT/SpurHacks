import pymongo
import uuid
from datetime import datetime, timezone

print("Creating promptly database...")

client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["promptly"]

# Users collection
users = db["users"]
users.drop()
test_user = {
    "_id": "demo-user-123",
    "email": "demo@promptly.com", 
    "username": "demo@promptly.com",
    "hashed_password": "$argon2id$v=19$m=102400,t=2,p=8$dummy_hash",
    "is_active": True,
    "is_superuser": False, 
    "is_verified": False,
    "first_name": "Demo",
    "last_name": "User",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "updated_at": datetime.now(timezone.utc).isoformat()
}
users.insert_one(test_user)
print("Users collection created")

# Sessions collection  
sessions = db["sessions"]
sessions.drop()
test_session = {
    "_id": "demo-session-123",
    "title": "Demo Session",
    "user_id": "demo-user-123", 
    "starter_prompt": "Welcome to Promptly!",
    "max_questions": 10,
    "target_model": "gemini-2.0-flash-exp",
    "status": "active",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "updated_at": datetime.now(timezone.utc).isoformat()
}
sessions.insert_one(test_session)
print("Sessions collection created")

# Nodes collection
nodes = db["nodes"]
nodes.drop()
test_node = {
    "_id": "demo-node-123",
    "session_id": "demo-session-123",
    "type": "question",
    "content": "What would you like to explore?",
    "parent_id": None,
    "children": [],
    "created_at": datetime.now(timezone.utc).isoformat()
}
nodes.insert_one(test_node)
print("Nodes collection created")

# Files collection
files = db["files"]
files.drop()
test_file = {
    "_id": "demo-file-123",
    "filename": "demo.txt",
    "original_filename": "demo.txt", 
    "content_type": "text/plain",
    "size": 1024,
    "user_id": "demo-user-123",
    "session_id": "demo-session-123",
    "storage_path": "/uploads/demo.txt",
    "uploaded_at": datetime.now(timezone.utc).isoformat()
}
files.insert_one(test_file)
print("Files collection created")

# Create indexes
users.create_index("email", unique=True)
users.create_index("username", unique=True)
sessions.create_index("user_id")
nodes.create_index("session_id")
files.create_index("user_id")

print("Database recreation complete!")
print("Collections created: users, sessions, nodes, files")
print("Connect MongoDB Compass to: mongodb://localhost:27017")

client.close() 