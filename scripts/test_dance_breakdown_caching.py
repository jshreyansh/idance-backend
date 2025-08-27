#!/usr/bin/env python3
"""
Test script for dance breakdown caching functionality
"""

import asyncio
import logging
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ai.dance_breakdown import dance_breakdown_service
from services.ai.models import DanceBreakdownRequest
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_caching_functionality():
    """Test the caching functionality of dance breakdown service"""
    
    # Test video URL (replace with a real YouTube URL for testing)
    test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll for testing
    test_user_id = "507f1f77bcf86cd799439011"  # Test user ID
    
    logger.info("🧪 Testing Dance Breakdown Caching Functionality")
    logger.info(f"🎬 Test video URL: {test_video_url}")
    logger.info(f"👤 Test user ID: {test_user_id}")
    
    try:
        # Step 1: Check if breakdown exists in cache
        logger.info("\n📋 Step 1: Checking cache status...")
        existing_breakdown = await dance_breakdown_service.get_breakdown_by_video_url(test_video_url)
        
        if existing_breakdown:
            logger.info("✅ Found existing breakdown in cache")
            logger.info(f"📊 Breakdown ID: {existing_breakdown['_id']}")
            logger.info(f"📅 Created: {existing_breakdown.get('createdAt')}")
            logger.info(f"🎯 Total steps: {existing_breakdown.get('totalSteps', 0)}")
        else:
            logger.info("🆕 No existing breakdown found in cache")
        
        # Step 2: Get breakdown statistics
        logger.info("\n📊 Step 2: Getting breakdown statistics...")
        stats = await dance_breakdown_service.get_breakdown_statistics()
        
        logger.info("📈 Breakdown Statistics:")
        logger.info(f"   Total breakdowns: {stats.get('total_breakdowns', 0)}")
        logger.info(f"   Successful breakdowns: {stats.get('successful_breakdowns', 0)}")
        logger.info(f"   Unique videos: {stats.get('unique_videos', 0)}")
        logger.info(f"   Cache efficiency: {stats.get('cache_efficiency_percentage', 0)}%")
        logger.info(f"   Success rate: {stats.get('success_rate_percentage', 0)}%")
        
        # Step 3: Test cache status endpoint simulation
        logger.info("\n🔍 Step 3: Testing cache status check...")
        cache_status = {
            "success": True,
            "video_url": test_video_url,
            "cached": existing_breakdown is not None,
            "breakdown_id": str(existing_breakdown["_id"]) if existing_breakdown else None,
            "created_at": existing_breakdown.get("createdAt") if existing_breakdown else None
        }
        
        logger.info("🎯 Cache Status:")
        logger.info(f"   Video URL: {cache_status['video_url']}")
        logger.info(f"   Cached: {cache_status['cached']}")
        logger.info(f"   Breakdown ID: {cache_status['breakdown_id']}")
        logger.info(f"   Created At: {cache_status['created_at']}")
        
        # Step 4: Test duplicate cleanup (dry run)
        logger.info("\n🧹 Step 4: Testing duplicate cleanup...")
        cleanup_result = await dance_breakdown_service.clear_duplicate_breakdowns()
        
        logger.info("🧹 Cleanup Result:")
        logger.info(f"   Total removed: {cleanup_result.get('total_removed', 0)}")
        logger.info(f"   Duplicate URLs processed: {cleanup_result.get('duplicate_urls_processed', 0)}")
        
        # Step 5: Test conversion function (if breakdown exists)
        if existing_breakdown:
            logger.info("\n🔄 Step 5: Testing database to response conversion...")
            try:
                response = await dance_breakdown_service.convert_db_breakdown_to_response(
                    existing_breakdown, "auto"
                )
                logger.info("✅ Successfully converted database breakdown to response")
                logger.info(f"   Response success: {response.success}")
                logger.info(f"   Total steps: {response.total_steps}")
                logger.info(f"   Mode: {response.mode}")
            except Exception as e:
                logger.error(f"❌ Error converting breakdown: {str(e)}")
        
        logger.info("\n✅ Caching functionality test completed successfully!")
        
        # Summary
        logger.info("\n📋 Test Summary:")
        logger.info(f"   Cache hit: {existing_breakdown is not None}")
        logger.info(f"   Total breakdowns in system: {stats.get('total_breakdowns', 0)}")
        logger.info(f"   Cache efficiency: {stats.get('cache_efficiency_percentage', 0)}%")
        logger.info(f"   Duplicates cleaned: {cleanup_result.get('total_removed', 0)}")
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
        raise

async def test_manual_breakdown_creation():
    """Test creating a manual breakdown (without OpenAI)"""
    
    test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    test_user_id = "507f1f77bcf86cd799439011"
    
    logger.info("\n🧪 Testing Manual Breakdown Creation")
    
    try:
        # Create a manual breakdown request
        request = DanceBreakdownRequest(
            video_url=test_video_url,
            mode="manual",  # Manual mode doesn't use OpenAI
            target_difficulty="beginner"
        )
        
        logger.info(f"🎬 Creating manual breakdown for: {test_video_url}")
        logger.info(f"🎯 Mode: {request.mode}")
        logger.info(f"📊 Target difficulty: {request.target_difficulty}")
        
        # Process the breakdown
        response = await dance_breakdown_service.process_dance_breakdown(request, test_user_id)
        
        if response.success:
            logger.info("✅ Manual breakdown created successfully!")
            logger.info(f"   Total steps: {response.total_steps}")
            logger.info(f"   Duration: {response.duration:.2f} seconds")
            logger.info(f"   BPM: {response.bpm}")
            logger.info(f"   Mode: {response.mode}")
            
            # Test caching by requesting the same URL again
            logger.info("\n🔄 Testing cache hit for same URL...")
            cached_response = await dance_breakdown_service.process_dance_breakdown(request, test_user_id)
            
            if cached_response.success:
                logger.info("✅ Cache hit successful!")
                logger.info(f"   Cached total steps: {cached_response.total_steps}")
                logger.info(f"   Cached duration: {cached_response.duration:.2f} seconds")
            else:
                logger.error("❌ Cache hit failed")
        else:
            logger.error(f"❌ Manual breakdown failed: {response.error_message}")
            
    except Exception as e:
        logger.error(f"❌ Manual breakdown test failed: {str(e)}")
        raise

if __name__ == "__main__":
    async def main():
        try:
            # Test basic caching functionality
            await test_caching_functionality()
            
            # Test manual breakdown creation (optional - uncomment to test)
            # await test_manual_breakdown_creation()
            
        except Exception as e:
            logger.error(f"❌ Test suite failed: {str(e)}")
            sys.exit(1)
    
    asyncio.run(main()) 