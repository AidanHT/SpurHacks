#!/usr/bin/env python3
"""
Recreate Promptly Database
Creates the database structure with collections and test data
"""

import os
import pymongo
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv

def recreate_database():
    print("🏗️  Recreating Promptly Database...")
    
    # Load environment variables
    load_dotenv()
    
    # Connect to MongoDB
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    client = pymongo.MongoClient(mongodb_url, serverSelectionTimeoutMS=5000)
    
    # Get/create the promptly database
    db = client["promptly"]
    
    print(f"📊 Working with database: promptly")
    
    # Create collections with initial documents
    collections_to_create = ["users", "sessions", "nodes", "files"]
    
    for collection_name in collections_to_create:
        collection = db[collection_name]
        
        # Drop collection if it exists to start fresh
        collection.drop()
        print(f"🗑️  Cleared {collection_name} collection")
        
        # Create the collection by inserting a document
        if collection_name == "users":
            # Create a test user
            test_user = {
                "_id": "test-user-" + str(uuid.uuid4())[:8],
                "email": "demo@promptly.com",
                "username": "demo@promptly.com",
                "hashed_password": "$argon2id$v=19$m=102400,t=2,p=8$dummy_hash_for_demo",
                "is_active": True,
                "is_superuser": False,
                "is_verified": False,
                "first_name": "Demo",
                "last_name": "User",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "source": "database_recreation"
            }
            collection.insert_one(test_user)
            print(f"✅ Created {collection_name} with demo user: {test_user['email']}")
            
        elif collection_name == "sessions":
            # Create a test session
            test_session = {
                "_id": "test-session-" + str(uuid.uuid4())[:8],
                "title": "Welcome to Promptly Demo Session",
                "user_id": "test-user-demo",
                "starter_prompt": "Hello! This is a demo session for testing the Promptly platform.",
                "max_questions": 10,
                "target_model": "gemini-2.0-flash-exp",
                "settings": {
                    "temperature": 0.7,
                    "max_tokens": 4096
                },
                "status": "active",
                "metadata": {
                    "created_by": "system",
                    "demo": True
                },
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "source": "database_recreation"
            }
            collection.insert_one(test_session)
            print(f"✅ Created {collection_name} with demo session: {test_session['title']}")
            
        elif collection_name == "nodes":
            # Create a test node
            test_node = {
                "_id": "test-node-" + str(uuid.uuid4())[:8],
                "session_id": "test-session-demo",
                "type": "question",
                "content": "What would you like to explore with AI prompting today?",
                "parent_id": None,
                "children": [],
                "metadata": {
                    "ai_generated": True,
                    "demo": True,
                    "order": 1
                },
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source": "database_recreation"
            }
            collection.insert_one(test_node)
            print(f"✅ Created {collection_name} with demo node: {test_node['content'][:50]}...")
            
        elif collection_name == "files":
            # Create a test file record
            test_file = {
                "_id": "test-file-" + str(uuid.uuid4())[:8],
                "filename": "demo_prompt_template.txt",
                "original_filename": "prompt_template.txt",
                "content_type": "text/plain",
                "size": 1024,
                "user_id": "test-user-demo",
                "session_id": "test-session-demo",
                "storage_path": "/uploads/demo/prompt_template.txt",
                "metadata": {
                    "demo": True,
                    "description": "Sample prompt template file"
                },
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
                "source": "database_recreation"
            }
            collection.insert_one(test_file)
            print(f"✅ Created {collection_name} with demo file: {test_file['filename']}")
    
    # Verify the recreation
    print("\n📊 Database Recreation Summary:")
    for collection_name in collections_to_create:
        count = db[collection_name].count_documents({})
        print(f"   {collection_name}: {count} document(s)")
    
    # Create indexes for better performance
    print("\n🔧 Creating database indexes...")
    
    # Users collection indexes
    db.users.create_index("email", unique=True)
    db.users.create_index("username", unique=True)
    print("✅ Users indexes created")
    
    # Sessions collection indexes
    db.sessions.create_index("user_id")
    db.sessions.create_index("created_at")
    print("✅ Sessions indexes created")
    
    # Nodes collection indexes
    db.nodes.create_index("session_id")
    db.nodes.create_index("parent_id")
    print("✅ Nodes indexes created")
    
    # Files collection indexes
    db.files.create_index("user_id")
    db.files.create_index("session_id")
    print("✅ Files indexes created")
    
    print(f"\n🎯 Database 'promptly' has been successfully recreated!")
    print(f"📍 Connection string: {mongodb_url}")
    print(f"🔗 You can now connect MongoDB Compass to: mongodb://localhost:27017")
    print(f"📁 Look for the 'promptly' database with 4 collections")
    
    client.close()

if __name__ == "__main__":
    recreate_database() 