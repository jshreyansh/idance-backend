#!/usr/bin/env python3
"""
Clear Video Data Only Script
This script clears only video-related data while preserving user accounts and other data
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

# Video-related collections to clear (these contain video data)
VIDEO_COLLECTIONS = [
    # Session system (contains video uploads)
    'dance_sessions',
    'dance_sessions_prod',
    'session_likes',
    'session_likes_prod',
    
    # Challenge system (contains video submissions)
    'challenge_submissions',
    'challenge_submissions_prod',
    'leaderboards',
    'leaderboards_prod',
    
    # AI and analysis (contains video analysis)
    'dance_breakdowns',
    'dance_breakdowns_prod',
    'pose_analysis',
    'pose_analysis_prod',
    
    # Feed system (contains video posts)
    'feed_items',
    'feed_items_prod',
]

# Collections to PRESERVE (user accounts, challenges, etc.)
PRESERVED_COLLECTIONS = [
    # User accounts and profiles
    'users',
    'users_prod',
    'user_stats',
    'user_stats_prod',
    'user_badges',
    'user_badges_prod',
    
    # Challenge definitions (not submissions)
    'challenges',
    'challenges_prod',
    
    # Background jobs
    'background_jobs',
    'background_jobs_prod',
    'job_queue',
    'job_queue_prod',
    
    # Rate limiting
    'rate_limits',
    'rate_limits_prod',
    'rate_limit_violations',
    'rate_limit_violations_prod',
]

async def clear_video_data_only():
    """Clear only video-related data while preserving user accounts and other data"""
    try:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[DB_NAME]
        
        print("🎬 Clearing Video Data Only...")
        print(f"📊 Database: {DB_NAME}")
        print(f"⏰ Timestamp: {datetime.utcnow()}")
        print(f"🎯 Target: Video-related collections only")
        
        # Step 1: List current collections
        print("\n📋 Current collections:")
        current_collections = await db.list_collection_names()
        for collection in sorted(current_collections):
            count = await db[collection].count_documents({})
            status = "🗑️  TO CLEAR" if collection in VIDEO_COLLECTIONS else "✅ PRESERVE"
            print(f"  - {collection}: {count} documents ({status})")
        
        # Step 2: Clear video-related collections
        print("\n🧹 Clearing video-related collections...")
        cleared_count = 0
        total_documents = 0
        
        for collection_name in VIDEO_COLLECTIONS:
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
        
        # Step 3: Clear S3 video files
        print("\n🗂️  Clearing S3 video files...")
        try:
            s3_client = boto3.client('s3')
            bucket_name = os.getenv('S3_BUCKET_NAME', 'idanceshreyansh')
            
            # List all objects in the bucket
            paginator = s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket_name)
            
            video_files = []
            for page in pages:
                for obj in page.get('Contents', []):
                    if obj['Key'].endswith('.mp4') or obj['Key'].endswith('.mov') or obj['Key'].endswith('.avi'):
                        video_files.append(obj['Key'])
            
            if video_files:
                print(f"  📹 Found {len(video_files)} video files in S3")
                
                # Delete video files
                for video_key in video_files:
                    try:
                        s3_client.delete_object(Bucket=bucket_name, Key=video_key)
                        print(f"    ✅ Deleted: {video_key}")
                    except Exception as e:
                        print(f"    ❌ Failed to delete {video_key}: {e}")
                
                print(f"  ✅ Cleared {len(video_files)} video files from S3")
            else:
                print(f"  ℹ️  No video files found in S3 bucket")
                
        except Exception as e:
            print(f"  ❌ Error clearing S3 files: {str(e)}")
        
        # Step 4: Final summary
        print("\n📊 Final collection status:")
        final_collections = await db.list_collection_names()
        for collection in sorted(final_collections):
            count = await db[collection].count_documents({})
            status = "🗑️  CLEARED" if collection in VIDEO_COLLECTIONS else "✅ PRESERVED"
            print(f"  - {collection}: {count} documents ({status})")
        
        print(f"\n✅ Video data cleared successfully!")
        print(f"📈 Summary:")
        print(f"  - Video collections cleared: {cleared_count}")
        print(f"  - Total video documents deleted: {total_documents}")
        print(f"  - User accounts preserved: ✅")
        print(f"  - Challenge definitions preserved: ✅")
        print(f"  - S3 video files cleared: ✅")
        
        print(f"\n⚠️  WARNING: Video data cannot be recovered!")
        print(f"📝 Next steps:")
        print(f"  1. Restart your production server")
        print(f"  2. Test video uploads with new mobile-compatible processing")
        print(f"  3. All new videos will use the resizing middleware")
        print(f"  4. Users can re-upload their videos with mobile compatibility")
        
    except Exception as e:
        print(f"❌ Error clearing video data: {str(e)}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    # Confirm before proceeding
    print("⚠️  WARNING: This will delete ALL video-related data!")
    print("This includes:")
    print("  - All dance sessions and video uploads")
    print("  - All challenge submissions")
    print("  - All dance breakdowns")
    print("  - All feed items with videos")
    print("  - All S3 video files")
    print("")
    print("This will PRESERVE:")
    print("  - All user accounts and profiles")
    print("  - All challenge definitions")
    print("  - All user statistics and badges")
    print("  - All background jobs")
    print("")
    
    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        asyncio.run(clear_video_data_only())
    else:
        print("❌ Operation cancelled.") 