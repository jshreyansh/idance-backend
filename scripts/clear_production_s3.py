#!/usr/bin/env python3
"""
Script to clear production S3 videos
Deletes all video files from S3 that are referenced in production collections
"""

import os
import sys
import asyncio
from datetime import datetime
from typing import List, Set
import boto3
from botocore.exceptions import ClientError

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infra.mongo import Database, connect_to_mongo, close_mongo_connection

class ProductionS3Cleaner:
    def __init__(self):
        self.db = Database.get_database()
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'idance')
        
        if not self.bucket_name:
            raise ValueError("S3_BUCKET_NAME environment variable is required")
    
    async def get_production_file_keys(self) -> Set[str]:
        """Extract all file keys from production collections"""
        file_keys = set()
        
        print("🔍 Extracting file keys from production collections...")
        
        # 1. Challenge submissions (production)
        submissions = await self.db.challenge_submissions_prod.find({}).to_list(length=None)
        for submission in submissions:
            if 'video' in submission and 'file_key' in submission['video']:
                file_keys.add(submission['video']['file_key'])
            if 'videoFileKey' in submission:
                file_keys.add(submission['videoFileKey'])
        
        print(f"  📹 Found {len([k for k in file_keys if 'challenges/' in k])} challenge submission videos")
        
        # 2. Dance sessions (production)
        sessions = await self.db.dance_sessions_prod.find({}).to_list(length=None)
        for session in sessions:
            if 'videoFileKey' in session and session['videoFileKey']:
                file_keys.add(session['videoFileKey'])
            if 'thumbnailFileKey' in session and session['thumbnailFileKey']:
                file_keys.add(session['thumbnailFileKey'])
        
        print(f"  💃 Found {len([k for k in file_keys if 'sessions/' in k or 'dance_sessions/' in k])} dance session videos")
        
        # 3. Dance breakdowns (production)
        breakdowns = await self.db.dance_breakdowns_prod.find({}).to_list(length=None)
        for breakdown in breakdowns:
            if 'videoFileKey' in breakdown and breakdown['videoFileKey']:
                file_keys.add(breakdown['videoFileKey'])
            if 'video_url' in breakdown and breakdown['video_url']:
                # Extract file key from URL if it's an S3 URL
                file_key = self._extract_file_key_from_url(breakdown['video_url'])
                if file_key:
                    file_keys.add(file_key)
        
        print(f"  🎬 Found {len([k for k in file_keys if 'dance-breakdowns/' in k])} dance breakdown videos")
        
        # 4. Challenges (demo videos)
        challenges = await self.db.challenges_prod.find({}).to_list(length=None)
        for challenge in challenges:
            if 'demoVideoFileKey' in challenge and challenge['demoVideoFileKey']:
                file_keys.add(challenge['demoVideoFileKey'])
        
        print(f"  🏆 Found {len([k for k in file_keys if 'challenges/demo/' in k])} challenge demo videos")
        
        # 5. Pose analysis (if any video files are stored)
        pose_analyses = await self.db.pose_analysis_prod.find({}).to_list(length=None)
        for analysis in pose_analyses:
            if 'videoFileKey' in analysis and analysis['videoFileKey']:
                file_keys.add(analysis['videoFileKey'])
        
        # Remove None/empty values
        file_keys = {key for key in file_keys if key and key.strip()}
        
        return file_keys
    
    def _extract_file_key_from_url(self, url: str) -> str:
        """Extract file key from S3 URL"""
        if not url or not url.startswith('http'):
            return None
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            
            # Handle different S3 URL formats
            if 's3.amazonaws.com' in parsed.netloc:
                # Format: https://bucket.s3.region.amazonaws.com/key
                path = parsed.path.lstrip('/')
                if path.startswith(self.bucket_name + '/'):
                    return path[len(self.bucket_name) + 1:]
                return path
            elif parsed.netloc == self.bucket_name + '.s3.amazonaws.com':
                # Format: https://bucket.s3.amazonaws.com/key
                return parsed.path.lstrip('/')
            else:
                # Custom domain format
                return parsed.path.lstrip('/')
        except Exception:
            return None
    
    def delete_s3_files(self, file_keys: Set[str]) -> dict:
        """Delete files from S3"""
        results = {
            'successful': 0,
            'failed': 0,
            'not_found': 0,
            'errors': []
        }
        
        if not file_keys:
            print("ℹ️  No files to delete")
            return results
        
        print(f"🗑️  Deleting {len(file_keys)} files from S3...")
        
        for file_key in file_keys:
            try:
                # Check if file exists first
                try:
                    self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
                except ClientError as e:
                    if e.response['Error']['Code'] == '404':
                        print(f"  ⚠️  File not found: {file_key}")
                        results['not_found'] += 1
                        continue
                    else:
                        raise e
                
                # Delete the file
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
                print(f"  ✅ Deleted: {file_key}")
                results['successful'] += 1
                
            except ClientError as e:
                error_msg = f"Failed to delete {file_key}: {str(e)}"
                print(f"  ❌ {error_msg}")
                results['errors'].append(error_msg)
                results['failed'] += 1
            except Exception as e:
                error_msg = f"Unexpected error deleting {file_key}: {str(e)}"
                print(f"  ❌ {error_msg}")
                results['errors'].append(error_msg)
                results['failed'] += 1
        
        return results
    
    async def clear_production_s3(self):
        """Main method to clear production S3 videos"""
        print("🚀 Starting Production S3 Cleanup...")
        print(f"📦 S3 Bucket: {self.bucket_name}")
        print(f"⏰ Timestamp: {datetime.now()}")
        print(f"🎯 Environment: production")
        print()
        
        # Get all file keys from production collections
        file_keys = await self.get_production_file_keys()
        
        if not file_keys:
            print("✅ No production videos found to delete!")
            return
        
        print(f"\n📊 Found {len(file_keys)} files to delete:")
        for key in sorted(file_keys):
            print(f"  - {key}")
        
        # Confirm deletion
        print(f"\n⚠️  WARNING: This will delete {len(file_keys)} files from S3!")
        print("This operation cannot be undone!")
        
        confirm = input("\nAre you sure you want to continue? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("❌ Operation cancelled")
            return
        
        print("\n🗑️  Starting S3 deletion...")
        
        # Delete files from S3
        results = self.delete_s3_files(file_keys)
        
        # Print summary
        print(f"\n📈 S3 Cleanup Summary:")
        print(f"  ✅ Successfully deleted: {results['successful']}")
        print(f"  ❌ Failed to delete: {results['failed']}")
        print(f"  ⚠️  Files not found: {results['not_found']}")
        
        if results['errors']:
            print(f"\n❌ Errors encountered:")
            for error in results['errors'][:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(results['errors']) > 5:
                print(f"  ... and {len(results['errors']) - 5} more errors")
        
        print(f"\n✅ Production S3 cleanup completed!")
        print(f"📝 Next steps:")
        print(f"  1. Verify S3 bucket is clean")
        print(f"  2. Restart production server if needed")
        print(f"  3. Test video upload functionality")

async def main():
    """Main entry point"""
    try:
        await connect_to_mongo()
        cleaner = ProductionS3Cleaner()
        await cleaner.clear_production_s3()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(main()) 