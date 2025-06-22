#!/usr/bin/env python3
"""
Simple integration test for the New Session feature.
Tests the session creation endpoint end-to-end.
"""

import asyncio
import httpx
import json

# Test data matching frontend form structure
TEST_SESSION_DATA = {
    "title": "Test Marketing Session",
    "starter_prompt": "Create a compelling marketing email for our new product launch targeting tech-savvy millennials.",
    "max_questions": 5,
    "target_model": "gemini-2.5",
    "settings": {
        "tone": "friendly",
        "wordLimit": 150,
        "contextSources": []
    }
}

async def test_session_creation():
    """Test session creation endpoint."""
    print("🧪 Testing Session Creation Endpoint...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Test POST /sessions
            response = await client.post(
                "http://localhost:8000/sessions",
                json=TEST_SESSION_DATA,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"📤 Request sent to: POST /sessions")
            print(f"📥 Response status: {response.status_code}")
            
            if response.status_code == 201:
                data = response.json()
                print(f"✅ Session created successfully!")
                print(f"📄 Session ID: {data['id']}")
                print(f"📝 Title: {data['title']}")
                print(f"🎯 Target Model: {data['target_model']}")
                print(f"⚙️  Settings: {data['settings']}")
                return True
            else:
                print(f"❌ Failed to create session")
                print(f"📄 Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            print("💡 Make sure the backend server is running on http://localhost:8000")
            return False

async def test_health_check():
    """Test basic health check endpoint."""
    print("🔍 Testing Health Check...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/ping")
            if response.status_code == 200:
                print("✅ Backend health check passed")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Backend not available: {e}")
            return False

async def main():
    """Run all integration tests."""
    print("🚀 Starting Integration Tests")
    print("=" * 50)
    
    # Test 1: Health Check
    health_ok = await test_health_check()
    print()
    
    if not health_ok:
        print("💥 Cannot proceed - backend is not available")
        return False
    
    # Test 2: Session Creation
    session_ok = await test_session_creation()
    print()
    
    # Results
    print("=" * 50)
    if health_ok and session_ok:
        print("🎉 ALL TESTS PASSED! New Session feature is working end-to-end")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1) 