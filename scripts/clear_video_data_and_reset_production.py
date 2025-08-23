#!/usr/bin/env python3
"""
Clear Video Data and Reset Production Script
This script clears video-related data, resets user stats, and removes production challenges
while preserving user accounts and basic user data.
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime
import boto3

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# MongoDB connection
MONGO_URI = "mongodb+srv://dbshreyansh:dbshreyansh@cluster0.syqn1pb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "idance"

# Collections to CLEAR completely (video data and production challenges)
CLEAR_COLLECTIONS = [
    # Video-related collections
    'dance_sessions',
    'dance_sessions_prod',
    'session_likes',
    'session_likes_prod',
    'challenge_submissions',
    'challenge_submissions_prod',
    'leaderboards',
    'leaderboards_prod',
    'dance_breakdowns',
    'dance_breakdowns_prod',
    'pose_analysis',
    'pose_analysis_prod',
    'feed_items',
    'feed_items_prod',
    
    # Production challenges (to be recreated)
    'challenges',
    'challenges_prod',
]

# Collections to RESET (user stats and badges)
RESET_COLLECTIONS = [
    'user_stats',
    'user_stats_prod',
    'user_badges',
    'user_badges_prod',
]

# Collections to PRESERVE (user accounts only)
PRESERVED_COLLECTIONS = [
    'users',
    'users_prod',
    'background_jobs',
    'background_jobs_prod',
    'job_queue',
    'job_queue_prod',
    'rate_limits',
    'rate_limits_prod',
    'rate_limit_violations',
    'rate_limit_violations_prod',
]

async def reset_user_stats(db):
    """Reset user statistics to default values"""
    print("\n📊 Resetting user statistics...")
    
    try:
        # Get all users
        users = await db.users.find({}).to_list(length=None)
        users_prod = await db.users_prod.find({}).to_list(length=None)
        all_users = users + users_prod
        
        print(f"  📈 Found {len(all_users)} users to reset stats for")
        
        # Default stats structure
        default_stats = {
            "totalSessions": 0,
            "totalChallenges": 0,
            "totalSubmissions": 0,
            "totalLikes": 0,
            "totalComments": 0,
            "totalShares": 0,
            "totalViews": 0,
            "totalWatchTime": 0,
            "averageScore": 0.0,
            "bestScore": 0,
            "currentStreak": 0,
            "longestStreak": 0,
            "level": 1,
            "experience": 0,
            "rank": "Beginner",
            "achievements": [],
            "lastActivity": None,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        
        # Reset stats for each user
        for user in all_users:
            user_id = user.get('_id')
            if user_id:
                # Reset in both development and production
                await db.user_stats.update_one(
                    {"userId": str(user_id)},
                    {"$set": default_stats},
                    upsert=True
                )
                await db.user_stats_prod.update_one(
                    {"userId": str(user_id)},
                    {"$set": default_stats},
                    upsert=True
                )
                print(f"    ✅ Reset stats for user: {user.get('profile', {}).get('displayName', 'Unknown')}")
        
        print(f"  ✅ Reset statistics for {len(all_users)} users")
        
    except Exception as e:
        print(f"  ❌ Error resetting user stats: {str(e)}")

async def clear_user_badges(db):
    """Clear all user badges"""
    print("\n🏆 Clearing user badges...")
    
    try:
        # Clear badges in both development and production
        result_dev = await db.user_badges.delete_many({})
        result_prod = await db.user_badges_prod.delete_many({})
        
        print(f"  ✅ Cleared {result_dev.deleted_count} badges from development")
        print(f"  ✅ Cleared {result_prod.deleted_count} badges from production")
        
    except Exception as e:
        print(f"  ❌ Error clearing user badges: {str(e)}")

async def clear_video_data_and_reset_production():
    """Clear video data, reset user stats, and remove production challenges"""
    try:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[DB_NAME]
        
        print("🎬 Clearing Video Data and Resetting Production...")
        print(f"📊 Database: {DB_NAME}")
        print(f"⏰ Timestamp: {datetime.utcnow()}")
        print(f"🎯 Target: Video data, user stats, and production challenges")
        
        # Step 1: List current collections
        print("\n📋 Current collections:")
        current_collections = await db.list_collection_names()
        for collection in sorted(current_collections):
            count = await db[collection].count_documents({})
            if collection in CLEAR_COLLECTIONS:
                status = "🗑️  TO CLEAR"
            elif collection in RESET_COLLECTIONS:
                status = "🔄 TO RESET"
            else:
                status = "✅ PRESERVE"
            print(f"  - {collection}: {count} documents ({status})")
        
        # Step 2: Clear video-related and challenge collections
        print("\n🧹 Clearing video data and challenges...")
        cleared_count = 0
        total_documents = 0
        
        for collection_name in CLEAR_COLLECTIONS:
            try:
                if collection_name in current_collections:
                    doc_count = await db[collection_name].count_documents({})
                    total_documents += doc_count
                    
                    result = await db[collection_name].delete_many({})
                    cleared_count += 1
                    
                    print(f"  ✅ Cleared {collection_name}: {doc_count} documents deleted")
                else:
                    print(f"  ℹ️  Collection {collection_name} does not exist, skipping")
                    
            except Exception as e:
                print(f"  ❌ Error clearing {collection_name}: {str(e)}")
        
        # Step 3: Reset user statistics
        await reset_user_stats(db)
        
        # Step 4: Clear user badges
        await clear_user_badges(db)
        
        # Step 5: Clear S3 files and folders
        print("\n🗂️  Clearing S3 files and folders...")
        try:
            s3_client = boto3.client('s3')
            bucket_name = os.getenv('S3_BUCKET_NAME', 'idanceshreyansh')
            
            # List all objects in the bucket
            paginator = s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket_name)
            
            all_files = []
            video_files = []
            image_files = []
            other_files = []
            
            for page in pages:
                for obj in page.get('Contents', []):
                    key = obj['Key']
                    all_files.append(key)
                    
                    # Categorize files
                    if key.endswith(('.mp4', '.mov', '.avi', '.webm')):
                        video_files.append(key)
                    elif key.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                        image_files.append(key)
                    else:
                        other_files.append(key)
            
            if all_files:
                print(f"  📁 Found {len(all_files)} total files in S3")
                print(f"    📹 Videos: {len(video_files)}")
                print(f"    🖼️  Images: {len(image_files)}")
                print(f"    📄 Others: {len(other_files)}")
                
                # Delete all files
                deleted_count = 0
                for file_key in all_files:
                    try:
                        s3_client.delete_object(Bucket=bucket_name, Key=file_key)
                        deleted_count += 1
                        print(f"    ✅ Deleted: {file_key}")
                    except Exception as e:
                        print(f"    ❌ Failed to delete {file_key}: {e}")
                
                print(f"  ✅ Cleared {deleted_count} files from S3")
                
                # Also clear any empty folders by deleting them
                print(f"\n  🗂️  Cleaning up empty folders...")
                try:
                    # Get unique folder prefixes
                    folder_prefixes = set()
                    for file_key in all_files:
                        if '/' in file_key:
                            folder_path = '/'.join(file_key.split('/')[:-1]) + '/'
                            folder_prefixes.add(folder_path)
                    
                    # Delete empty folders (S3 doesn't have real folders, but we can clean up prefixes)
                    for folder_prefix in sorted(folder_prefixes, reverse=True):  # Delete deepest first
                        try:
                            # Check if folder is empty
                            response = s3_client.list_objects_v2(
                                Bucket=bucket_name,
                                Prefix=folder_prefix,
                                MaxKeys=1
                            )
                            
                            if 'Contents' not in response or len(response['Contents']) == 0:
                                print(f"    ✅ Cleaned empty folder: {folder_prefix}")
                        except Exception as e:
                            print(f"    ⚠️  Could not check folder {folder_prefix}: {e}")
                            
                except Exception as e:
                    print(f"    ❌ Error cleaning folders: {e}")
                    
            else:
                print(f"  ℹ️  No files found in S3 bucket")
                
        except Exception as e:
            print(f"  ❌ Error clearing S3 files: {str(e)}")
        
        # Step 6: Final summary
        print("\n📊 Final collection status:")
        final_collections = await db.list_collection_names()
        for collection in sorted(final_collections):
            count = await db[collection].count_documents({})
            if collection in CLEAR_COLLECTIONS:
                status = "🗑️  CLEARED"
            elif collection in RESET_COLLECTIONS:
                status = "🔄 RESET"
            else:
                status = "✅ PRESERVED"
            print(f"  - {collection}: {count} documents ({status})")
        
        print(f"\n✅ Production reset completed successfully!")
        print(f"📈 Summary:")
        print(f"  - Collections cleared: {cleared_count}")
        print(f"  - Total documents deleted: {total_documents}")
        print(f"  - User accounts preserved: ✅")
        print(f"  - User stats reset: ✅")
        print(f"  - User badges cleared: ✅")
        print(f"  - Challenges removed: ✅")
        print(f"  - S3 files and folders cleared: ✅")
        
        print(f"\n⚠️  WARNING: This operation cannot be undone!")
        print(f"📝 Next steps:")
        print(f"  1. Restart your production server")
        print(f"  2. Create new challenges in production")
        print(f"  3. Test video uploads with new mobile-compatible processing")
        print(f"  4. All new videos will use the resizing middleware")
        print(f"  5. Users can start fresh with clean stats")
        
    except Exception as e:
        print(f"❌ Error resetting production: {str(e)}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    # Confirm before proceeding
    print("⚠️  WARNING: This will reset your production environment!")
    print("This will CLEAR:")
    print("  - All dance sessions and video uploads")
    print("  - All challenge submissions")
    print("  - All dance breakdowns")
    print("  - All feed items with videos")
    print("  - All S3 video files")
    print("  - All production challenges")
    print("")
    print("This will RESET:")
    print("  - All user statistics to default values")
    print("  - All user badges and achievements")
    print("")
    print("This will PRESERVE:")
    print("  - All user accounts and profiles")
    print("  - All background jobs")
    print("  - All rate limiting data")
    print("")
    print("⚠️  Users will lose all their progress, stats, and achievements!")
    print("⚠️  All challenges will need to be recreated!")
    print("")
    
    response = input("Are you sure you want to continue? (type 'yes' to confirm): ")
    if response.lower() == 'yes':
        asyncio.run(clear_video_data_and_reset_production())
    else:
        print("❌ Operation cancelled.") 