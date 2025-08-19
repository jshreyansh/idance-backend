#!/usr/bin/env python3
"""
Database Environment Setup Script
This script sets up separate collections for production and test environments
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# MongoDB connection
MONGO_URI = "mongodb+srv://dbshreyansh:dbshreyansh@cluster0.syqn1pb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "idance"

# Collection mappings
COLLECTION_MAPPINGS = {
    # Core collections
    'users': 'users',
    'user_stats': 'user_stats',
    'user_badges': 'user_badges',
    
    # Challenge system
    'challenges': 'challenges',
    'challenge_submissions': 'challenge_submissions',
    'leaderboards': 'leaderboards',
    
    # Session system
    'dance_sessions': 'dance_sessions',
    'session_likes': 'session_likes',
    
    # AI and analysis
    'dance_breakdowns': 'dance_breakdowns',
    'pose_analysis': 'pose_analysis',
    
    # Feed system
    'feed_items': 'feed_items',
    
    # Background jobs
    'background_jobs': 'background_jobs',
    'job_queue': 'job_queue'
}

async def setup_database_environments():
    """Set up separate collections for production and test environments"""
    try:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[DB_NAME]
        
        print("🚀 Setting up database environments...")
        print(f"📊 Database: {DB_NAME}")
        print(f"⏰ Timestamp: {datetime.utcnow()}")
        
        # Step 1: List current collections
        print("\n📋 Current collections:")
        current_collections = await db.list_collection_names()
        for collection in sorted(current_collections):
            count = await db[collection].count_documents({})
            print(f"  - {collection}: {count} documents")
        
        # Step 2: Create production collections and migrate data
        print("\n🔄 Setting up PRODUCTION collections...")
        await setup_environment_collections(db, 'production', current_collections)
        
        # Step 3: Create test collections (empty)
        print("\n🧪 Setting up TEST collections...")
        await setup_environment_collections(db, 'test', current_collections, migrate_data=False)
        
        # Step 4: Create development collections (migrate data)
        print("\n💻 Setting up DEVELOPMENT collections...")
        # Skip development setup since collections already exist
        print("  ℹ️  Development collections already exist, skipping migration")
        
        # Step 5: Create indexes for all environments
        print("\n🔧 Creating indexes for all environments...")
        await create_indexes_for_all_environments(db)
        
        # Step 6: Summary
        print("\n📊 Final collection summary:")
        final_collections = await db.list_collection_names()
        for collection in sorted(final_collections):
            count = await db[collection].count_documents({})
            print(f"  - {collection}: {count} documents")
        
        print("\n✅ Database environment setup completed successfully!")
        print("\n📝 Next steps:")
        print("1. Set ENVIRONMENT=production for production deployment")
        print("2. Set ENVIRONMENT=test for testing")
        print("3. Set ENVIRONMENT=development for development (default)")
        print("4. Update your .env file with the appropriate ENVIRONMENT variable")
        
    except Exception as e:
        print(f"❌ Error setting up database environments: {str(e)}")
        raise
    finally:
        client.close()

async def setup_environment_collections(db, environment: str, current_collections: list, migrate_data: bool = True):
    """Set up collections for a specific environment"""
    suffix = '_prod' if environment == 'production' else '_test' if environment == 'test' else ''
    
    for base_name, collection_name in COLLECTION_MAPPINGS.items():
        env_collection_name = f"{collection_name}{suffix}"
        
        # Check if collection exists in current data
        if collection_name in current_collections:
            if migrate_data:
                # Migrate data from current collection to environment-specific collection
                print(f"  📦 Migrating {collection_name} -> {env_collection_name}")
                await migrate_collection_data(db, collection_name, env_collection_name)
            else:
                # Create empty collection for test environment
                print(f"  📦 Creating empty {env_collection_name}")
                await create_empty_collection(db, env_collection_name)
        else:
            # Create new collection
            print(f"  📦 Creating new {env_collection_name}")
            await create_empty_collection(db, env_collection_name)

async def migrate_collection_data(db, source_collection: str, target_collection: str):
    """Migrate data from source collection to target collection"""
    try:
        # Get all documents from source collection
        documents = await db[source_collection].find({}).to_list(length=None)
        
        if documents:
            # Insert documents into target collection
            result = await db[target_collection].insert_many(documents)
            print(f"    ✅ Migrated {len(result.inserted_ids)} documents")
        else:
            print(f"    ℹ️  No documents to migrate")
            
    except Exception as e:
        print(f"    ❌ Error migrating {source_collection}: {str(e)}")

async def create_empty_collection(db, collection_name: str):
    """Create an empty collection with basic structure"""
    try:
        # Insert and immediately delete a document to create the collection
        result = await db[collection_name].insert_one({"__temp__": True, "created_at": datetime.utcnow()})
        await db[collection_name].delete_one({"_id": result.inserted_id})
        print(f"    ✅ Created empty collection")
    except Exception as e:
        print(f"    ❌ Error creating {collection_name}: {str(e)}")

async def create_indexes_for_all_environments(db):
    """Create indexes for all environment collections"""
    environments = ['_prod', '_test']  # Skip development since it already has indexes
    
    for env_suffix in environments:
        print(f"  🔧 Creating indexes for {env_suffix} environment...")
        
        try:
            # Users indexes
            users_collection = f"users{env_suffix}"
            await db[users_collection].create_index([("auth.email", 1)], unique=True, sparse=True)
            await db[users_collection].create_index([("auth.providerId", 1)], sparse=True)
            await db[users_collection].create_index([("profile.username", 1)], unique=True, sparse=True)
            
            # User stats indexes (skip unique constraint for now due to data issues)
            user_stats_collection = f"user_stats{env_suffix}"
            await db[user_stats_collection].create_index([("userId", 1)], sparse=True)
            
            # Challenges indexes
            challenges_collection = f"challenges{env_suffix}"
            await db[challenges_collection].create_index([("isActive", 1), ("startTime", 1), ("endTime", 1)])
            await db[challenges_collection].create_index([("type", 1), ("difficulty", 1)])
            await db[challenges_collection].create_index([("createdBy", 1), ("createdAt", -1)])
            
            # Challenge submissions indexes
            submissions_collection = f"challenge_submissions{env_suffix}"
            await db[submissions_collection].create_index([("userId", 1), ("challengeId", 1)])
            await db[submissions_collection].create_index([("challengeId", 1), ("totalScore", -1)])
            await db[submissions_collection].create_index([("submittedAt", -1)])
            
            # Dance sessions indexes
            sessions_collection = f"dance_sessions{env_suffix}"
            await db[sessions_collection].create_index([("userId", 1), ("startTime", -1)])
            await db[sessions_collection].create_index([("isPublic", 1), ("sharedToFeed", 1)])
            await db[sessions_collection].create_index([("status", 1)])
            
            # Dance breakdowns indexes
            breakdowns_collection = f"dance_breakdowns{env_suffix}"
            await db[breakdowns_collection].create_index([("userId", 1), ("createdAt", -1)])
            await db[breakdowns_collection].create_index([("videoUrl", 1)])
            await db[breakdowns_collection].create_index([("success", 1)])
            
            print(f"    ✅ Indexes created for {env_suffix}")
        except Exception as e:
            print(f"    ⚠️  Warning creating indexes for {env_suffix}: {str(e)}")
            continue

async def cleanup_old_collections(db, current_collections: list):
    """Clean up old collections after migration (optional)"""
    print("\n🧹 Cleaning up old collections...")
    
    # List of collections to potentially clean up
    old_collections = [
        'users', 'user_stats', 'challenges', 'challenge_submissions',
        'dance_sessions', 'dance_breakdowns', 'session_likes'
    ]
    
    for collection in old_collections:
        if collection in current_collections:
            count = await db[collection].count_documents({})
            print(f"  📊 {collection}: {count} documents")
            
            # Ask for confirmation before deletion
            # For now, we'll just show what would be deleted
            print(f"    ⚠️  Would delete {collection} (not actually deleting for safety)")

async def main():
    """Main function"""
    try:
        # Load environment variables
        load_dotenv()
        
        print("🚀 Database Environment Setup Script")
        print("=" * 50)
        
        # Run the setup
        await setup_database_environments()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 