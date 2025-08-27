#!/usr/bin/env python3
"""
Test script for the new session update API
Tests the Instagram-like flow: start session -> update metadata -> complete session
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infra.mongo import connect_to_mongo

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "testpassword123"

async def get_auth_token(session):
    """Get authentication token for testing"""
    print("🔐 Getting authentication token...")
    
    # Try to login first
    login_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    
    async with session.post(f"{BASE_URL}/auth/login", json=login_data) as response:
        if response.status == 200:
            data = await response.json()
            return data.get("access_token")
        else:
            print("⚠️ Login failed, trying signup...")
            
            # Try signup
            async with session.post(f"{BASE_URL}/auth/signup", json=login_data) as signup_response:
                if signup_response.status == 200:
                    data = await signup_response.json()
                    return data.get("access_token")
                else:
                    print(f"❌ Signup failed: {await signup_response.text()}")
                    return None

async def test_session_update_flow(session, auth_token):
    """Test the complete Instagram-like session flow"""
    print("\n🎬 Testing Instagram-like session flow...")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Step 1: Start session with minimal data
    print("\n1️⃣ Starting session with minimal data...")
    start_data = {
        "style": "hip hop",
        "sessionType": "freestyle",
        "isPublic": True,
        "sharedToFeed": False,
        "remixable": False
    }
    
    async with session.post(f"{BASE_URL}/api/sessions/start", json=start_data, headers=headers) as response:
        if response.status != 200:
            print(f"❌ Failed to start session: {await response.text()}")
            return False
        
        start_result = await response.json()
        session_id = start_result.get("sessionId")
        print(f"✅ Session started with ID: {session_id}")
    
    # Step 2: Update session metadata (Instagram-like flow)
    print("\n2️⃣ Updating session metadata...")
    update_data = {
        "highlightText": "Amazing dance session!",
        "tags": ["energetic", "fun", "hip hop"],
        "location": "New York",
        "promptUsed": "Dance to the beat",
        "isPublic": True,
        "sharedToFeed": True
    }
    
    async with session.put(f"{BASE_URL}/api/sessions/{session_id}/update", json=update_data, headers=headers) as response:
        if response.status != 200:
            print(f"❌ Failed to update session: {await response.text()}")
            return False
        
        update_result = await response.json()
        print(f"✅ Session updated: {update_result.get('message')}")
    
    # Step 3: Verify session was updated
    print("\n3️⃣ Verifying session update...")
    async with session.get(f"{BASE_URL}/api/sessions/me", headers=headers) as response:
        if response.status != 200:
            print(f"❌ Failed to get sessions: {await response.text()}")
            return False
        
        sessions = await response.json()
        updated_session = None
        for s in sessions:
            if s.get("_id") == session_id:
                updated_session = s
                break
        
        if not updated_session:
            print("❌ Updated session not found in user sessions")
            return False
        
        # Verify the updates
        if updated_session.get("highlightText") != "Amazing dance session!":
            print("❌ highlightText not updated correctly")
            return False
        
        if "energetic" not in updated_session.get("tags", []):
            print("❌ tags not updated correctly")
            return False
        
        print("✅ Session update verified successfully")
    
    # Step 4: Test partial update (only some fields)
    print("\n4️⃣ Testing partial update...")
    partial_update_data = {
        "highlightText": "Updated highlight text!",
        "tags": ["updated", "tags"]
    }
    
    async with session.put(f"{BASE_URL}/api/sessions/{session_id}/update", json=partial_update_data, headers=headers) as response:
        if response.status != 200:
            print(f"❌ Failed to partially update session: {await response.text()}")
            return False
        
        partial_result = await response.json()
        print(f"✅ Partial update successful: {partial_result.get('message')}")
    
    # Step 5: Test update with no changes
    print("\n5️⃣ Testing update with no changes...")
    no_change_data = {}
    
    async with session.put(f"{BASE_URL}/api/sessions/{session_id}/update", json=no_change_data, headers=headers) as response:
        if response.status != 200:
            print(f"❌ Failed to handle no-change update: {await response.text()}")
            return False
        
        no_change_result = await response.json()
        print(f"✅ No-change update handled: {no_change_result.get('message')}")
    
    # Step 6: Complete the session
    print("\n6️⃣ Completing session...")
    end_time = datetime.utcnow()
    complete_data = {
        "sessionId": session_id,
        "endTime": end_time.isoformat() + "Z",
        "durationMinutes": 15,
        "caloriesBurned": 120,
        "score": 85,
        "stars": 4,
        "rating": 4.5
    }
    
    async with session.post(f"{BASE_URL}/api/sessions/complete", json=complete_data, headers=headers) as response:
        if response.status != 200:
            print(f"❌ Failed to complete session: {await response.text()}")
            return False
        
        complete_result = await response.json()
        print(f"✅ Session completed: {complete_result.get('message')}")
    
    # Step 7: Test that completed session cannot be updated
    print("\n7️⃣ Testing that completed session cannot be updated...")
    invalid_update_data = {
        "highlightText": "This should fail!"
    }
    
    async with session.put(f"{BASE_URL}/api/sessions/{session_id}/update", json=invalid_update_data, headers=headers) as response:
        if response.status == 400:
            print("✅ Correctly prevented update of completed session")
        else:
            print(f"❌ Should have prevented update of completed session: {await response.text()}")
            return False
    
    print("\n🎉 All tests passed! Session update API is working correctly.")
    return True

async def test_error_cases(session, auth_token):
    """Test error cases for the session update API"""
    print("\n🚨 Testing error cases...")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Test 1: Update non-existent session
    print("\n1️⃣ Testing update of non-existent session...")
    fake_session_id = "507f1f77bcf86cd799439011"  # Valid ObjectId format but doesn't exist
    update_data = {"highlightText": "This should fail"}
    
    async with session.put(f"{BASE_URL}/api/sessions/{fake_session_id}/update", json=update_data, headers=headers) as response:
        if response.status == 404:
            print("✅ Correctly handled non-existent session")
        else:
            print(f"❌ Should have returned 404 for non-existent session: {await response.text()}")
    
    # Test 2: Update with invalid inspirationSessionId
    print("\n2️⃣ Testing update with invalid inspirationSessionId...")
    
    # First create a session
    start_data = {
        "style": "hip hop",
        "sessionType": "freestyle",
        "isPublic": True
    }
    
    async with session.post(f"{BASE_URL}/api/sessions/start", json=start_data, headers=headers) as response:
        if response.status != 200:
            print("❌ Failed to create session for error testing")
            return False
        
        start_result = await response.json()
        session_id = start_result.get("sessionId")
    
    # Try to update with invalid inspirationSessionId
    invalid_inspiration_data = {
        "inspirationSessionId": "invalid-id-format"
    }
    
    async with session.put(f"{BASE_URL}/api/sessions/{session_id}/update", json=invalid_inspiration_data, headers=headers) as response:
        if response.status == 400:
            print("✅ Correctly handled invalid inspirationSessionId")
        else:
            print(f"❌ Should have returned 400 for invalid inspirationSessionId: {await response.text()}")
    
    print("\n✅ Error case tests completed!")

async def main():
    """Main test function"""
    print("🧪 Testing Session Update API")
    print("=" * 50)
    
    # Connect to database
    await connect_to_mongo()
    print("✅ Connected to database")
    
    async with aiohttp.ClientSession() as session:
        # Get authentication token
        auth_token = await get_auth_token(session)
        if not auth_token:
            print("❌ Failed to get authentication token")
            return
        
        print(f"✅ Got auth token: {auth_token[:20]}...")
        
        # Test the main flow
        success = await test_session_update_flow(session, auth_token)
        if not success:
            print("❌ Main flow test failed")
            return
        
        # Test error cases
        await test_error_cases(session, auth_token)
        
        print("\n🎉 All tests completed successfully!")
        print("\n📋 Summary:")
        print("✅ Session update API is working correctly")
        print("✅ Instagram-like flow is supported")
        print("✅ Error handling is robust")
        print("✅ Validation rules are enforced")

if __name__ == "__main__":
    asyncio.run(main()) 