#!/usr/bin/env python3
"""
Script to regenerate thumbnails for existing dance breakdowns
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ai.dance_breakdown import dance_breakdown_service
from infra.mongo import connect_to_mongo, close_mongo_connection

async def main():
    """Main function to regenerate thumbnails"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Connect to MongoDB
        await connect_to_mongo()
        print("✅ Connected to MongoDB")
        
        # Regenerate missing thumbnails
        print("🔄 Starting thumbnail regeneration...")
        result = await dance_breakdown_service.regenerate_missing_thumbnails()
        
        print(f"✅ Thumbnail regeneration completed!")
        print(f"📊 Results:")
        print(f"   - Total processed: {result['total_processed']}")
        print(f"   - Success count: {result['success_count']}")
        print(f"   - Failed count: {result['failed_count']}")
        
        if result['failed_count'] > 0:
            print(f"⚠️  {result['failed_count']} thumbnails failed to generate. Check logs for details.")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
    finally:
        # Close MongoDB connection
        await close_mongo_connection()
        print("✅ MongoDB connection closed")

if __name__ == "__main__":
    asyncio.run(main()) 