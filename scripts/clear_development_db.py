#!/usr/bin/env python3
"""
Clear Development Database Script
This script clears all collections in the development environment
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

# Development collections to clear (base names without _prod or _test suffix)
DEVELOPMENT_COLLECTIONS = [
    # Core collections
    'users',
    'user_stats', 
    'user_badges',
    
    # Challenge system
    'challenges',
    'challenge_submissions',
    'leaderboards',
    
    # Session system
    'dance_sessions',
    'session_likes',
    
    # AI and analysis
    'dance_breakdowns',
    'pose_analysis',
    
    # Feed system
    'feed_items',
    
    # Background jobs
    'background_jobs',
    'job_queue',
    
    # Rate limiting
    'rate_limits',
    'rate_limit_violations'
]

async def clear_development_database():
    """Clear all development database collections"""
    try:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[DB_NAME]
        
        print("🗑️  Clearing Development Database...")
        print(f"📊 Database: {DB_NAME}")
        print(f"⏰ Timestamp: {datetime.utcnow()}")
        print(f"🎯 Environment: development")
        
        # Step 1: List current collections
        print("\n📋 Current collections before clearing:")
        current_collections = await db.list_collection_names()
        for collection in sorted(current_collections):
            count = await db[collection].count_documents({})
            print(f"  - {collection}: {count} documents")
        
        # Step 2: Clear development collections
        print("\n🧹 Clearing development collections...")
        cleared_count = 0
        total_documents = 0
        
        for collection_name in DEVELOPMENT_COLLECTIONS:
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
        
        # Step 3: Clear any other collections that might be development-related
        print("\n🔍 Checking for other development collections...")
        for collection in current_collections:
            # Skip production and test collections
            if collection.endswith('_prod') or collection.endswith('_test'):
                continue
                
            # Skip already cleared collections
            if collection in DEVELOPMENT_COLLECTIONS:
                continue
                
            # Clear any other collections that don't have environment suffixes
            try:
                doc_count = await db[collection].count_documents({})
                if doc_count > 0:
                    await db[collection].delete_many({})
                    total_documents += doc_count
                    cleared_count += 1
                    print(f"  ✅ Cleared additional collection {collection}: {doc_count} documents deleted")
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
        
        print(f"\n✅ Development database cleared successfully!")
        print(f"📈 Summary:")
        print(f"  - Collections cleared: {cleared_count}")
        print(f"  - Total documents deleted: {total_documents}")
        print(f"  - Remaining collections: {len(final_collections)}")
        
        print(f"\n⚠️  WARNING: This operation cannot be undone!")
        print(f"📝 Next steps:")
        print(f"  1. Restart your development server")
        print(f"  2. Test your application with clean data")
        print(f"  3. Consider running setup script if needed: python scripts/setup_database_environments.py")
        
    except Exception as e:
        print(f"❌ Error clearing development database: {str(e)}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    # Confirm before proceeding
    print("⚠️  WARNING: This will delete ALL data in development collections!")
    print("This includes:")
    print("  - All user accounts")
    print("  - All dance sessions")
    print("  - All challenges and submissions")
    print("  - All dance breakdowns")
    print("  - All feed items")
    print("  - All user statistics")
    print("  - All background jobs")
    print("")
    
    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        asyncio.run(clear_development_database())
    else:
        print("❌ Operation cancelled.") 