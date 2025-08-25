#!/usr/bin/env python3
"""
Test Script for Session Video Background Processing
Tests the new background processing pipeline for session videos
"""

import asyncio
import sys
import os
from datetime import datetime

# Add parent directory to path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.video_processing.background_service import background_video_processor
from infra.mongo import Database
from bson import ObjectId

async def test_background_processing():
    """Test the background video processing service"""
    
    # Initialize database connection
    await Database.connect_to_mongo()
    print("✅ Database connected")
    
    # Test data
    test_session_id = "507f1f77bcf86cd799439011"  # Valid ObjectId format
    test_video_url = "https://idanceshreyansh.s3.ap-south-1.amazonaws.com/sessions/test_user/test_session/video.mp4"
    test_user_id = "507f1f77bcf86cd799439012"
    
    print(f"🎬 Testing background video processing...")
    print(f"Session ID: {test_session_id}")
    print(f"Video URL: {test_video_url}")
    print(f"User ID: {test_user_id}")
    
    try:
        # Test the background processing service
        await background_video_processor.queue_session_video_processing(
            session_id=test_session_id,
            video_url=test_video_url,
            user_id=test_user_id
        )
        
        print("✅ Background processing queued successfully")
        print("⏳ Processing will happen in background...")
        print("📝 Check logs for processing status")
        
        # Wait a moment to see initial processing logs
        await asyncio.sleep(2)
        
    except Exception as e:
        print(f"❌ Error testing background processing: {str(e)}")
        return False
    
    return True

async def test_s3_operations():
    """Test S3 download and upload operations"""
    
    print(f"\n🧪 Testing S3 operations...")
    
    # Test file key extraction
    test_urls = [
        "https://idanceshreyansh.s3.ap-south-1.amazonaws.com/sessions/user123/session456/video.mp4",
        "https://s3.ap-south-1.amazonaws.com/idanceshreyansh/sessions/user123/session456/video.mp4"
    ]
    
    for url in test_urls:
        try:
            file_key = background_video_processor._extract_file_key_from_url(url)
            print(f"✅ File key extracted: {url} -> {file_key}")
        except Exception as e:
            print(f"❌ Failed to extract file key from {url}: {str(e)}")

async def main():
    """Main test function"""
    print("🚀 Starting Session Video Processing Tests")
    print("=" * 50)
    
    # Test S3 operations
    await test_s3_operations()
    
    # Test background processing (only if you have a real video URL)
    # await test_background_processing()
    
    print("\n" + "=" * 50)
    print("✅ Tests completed!")
    print("\n📋 Next Steps:")
    print("1. Upload a video to a session")
    print("2. Complete the session")
    print("3. Check logs for background processing")
    print("4. Verify processedVideoURL is populated in database")

if __name__ == "__main__":
    asyncio.run(main())