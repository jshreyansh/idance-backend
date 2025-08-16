#!/usr/bin/env python3
"""
Clear Production Database Script
This script clears all collections in the production environment
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URI = "mongodb+srv://dbshreyansh:dbshreyansh@cluster0.syqn1pb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "idance"

# Production collections to clear (collections with _prod suffix)
PRODUCTION_COLLECTIONS = [
    # Core collections
    'users_prod',
    'user_stats_prod', 
    'user_badges_prod',
    
    # Challenge system
    'challenges_prod',
    'challenge_submissions_prod',
    'leaderboards_prod',
    
    # Session system
    'dance_sessions_prod',
    'session_likes_prod',
    
    # AI and analysis
    'dance_breakdowns_prod',
    'pose_analysis_prod',
    
    # Feed system
    'feed_items_prod',
    
    # Background jobs
    'background_jobs_prod',
    'job_queue_prod',
    
    # Rate limiting
    'rate_limits_prod',
    'rate_limit_violations_prod'
]

async def clear_production_database():
    """Clear all production database collections"""
    try:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[DB_NAME]
        
        print("🗑️  Clearing Production Database...")
        print(f"📊 Database: {DB_NAME}")
        print(f"⏰ Timestamp: {datetime.utcnow()}")
        print(f"🎯 Environment: production")
        
        # Step 1: List current collections
        print("\n📋 Current collections before clearing:")
        current_collections = await db.list_collection_names()
        for collection in sorted(current_collections):
            count = await db[collection].count_documents({})
            print(f"  - {collection}: {count} documents")
        
        # Step 2: Clear production collections
        print("\n🧹 Clearing production collections...")
        cleared_count = 0
        total_documents = 0
        
        for collection_name in PRODUCTION_COLLECTIONS:
            try:
                # Check if collection exists
                if collection_name in current_collections:
                    # Get document count before clearing
                    doc_count = await db[collection_name].count_documents({})
                    total_documents += doc_count
                    
                    # Clear the collection
                    result = await db[collection_name].delete_many({})
                    cleared_count += 1
                    
                    print(f"  ✅ Cleared {collection_name}: {doc_count} documents deleted")
                else:
                    print(f"  ℹ️  Collection {collection_name} does not exist, skipping")
                    
            except Exception as e:
                print(f"  ❌ Error clearing {collection_name}: {str(e)}")
        
        # Step 3: Clear any other collections that might be production-related
        print("\n🔍 Checking for other production collections...")
        for collection in current_collections:
            # Skip development and test collections
            if collection.endswith('_test') or (not collection.endswith('_prod') and not collection in PRODUCTION_COLLECTIONS):
                continue
                
            # Skip already cleared collections
            if collection in PRODUCTION_COLLECTIONS:
                continue
                
            # Clear any other collections that have _prod suffix
            if collection.endswith('_prod'):
                try:
                    doc_count = await db[collection].count_documents({})
                    if doc_count > 0:
                        await db[collection].delete_many({})
                        total_documents += doc_count
                        cleared_count += 1
                        print(f"  ✅ Cleared additional production collection {collection}: {doc_count} documents deleted")
                    else:
                        print(f"  ℹ️  Collection {collection} is already empty")
                except Exception as e:
                    print(f"  ❌ Error clearing {collection}: {str(e)}")
        
        # Step 4: Final summary
        print("\n📊 Final collection status:")
        final_collections = await db.list_collection_names()
        for collection in sorted(final_collections):
            count = await db[collection].count_documents({})
            print(f"  - {collection}: {count} documents")
        
        print(f"\n✅ Production database cleared successfully!")
        print(f"📈 Summary:")
        print(f"  - Collections cleared: {cleared_count}")
        print(f"  - Total documents deleted: {total_documents}")
        print(f"  - Remaining collections: {len(final_collections)}")
        
        print(f"\n⚠️  WARNING: This operation cannot be undone!")
        print(f"📝 Next steps:")
        print(f"  1. Restart your production server")
        print(f"  2. Test your production application with clean data")
        print(f"  3. Consider running setup script if needed: python scripts/setup_database_environments.py")
        
    except Exception as e:
        print(f"❌ Error clearing production database: {str(e)}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    # Confirm before proceeding
    print("⚠️  WARNING: This will delete ALL data in production collections!")
    print("This includes:")
    print("  - All production user accounts")
    print("  - All production dance sessions")
    print("  - All production challenges and submissions")
    print("  - All production dance breakdowns")
    print("  - All production feed items")
    print("  - All production user statistics")
    print("  - All production background jobs")
    print("")
    
    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        asyncio.run(clear_production_database())
    else:
        print("❌ Operation cancelled.") 