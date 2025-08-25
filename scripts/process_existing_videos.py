#!/usr/bin/env python3
"""
Bulk Video Processing Script for Mobile Compatibility
Processes existing videos in the database to ensure mobile compatibility
"""

import asyncio
import logging
import os
import sys
from typing import List, Dict, Any
from datetime import datetime

# Add parent directory to path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infra.mongo import Database
from services.ai.dance_breakdown import DanceBreakdownService
from services.video_processing.middleware import video_resizing_middleware
from bson import ObjectId

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('video_processing.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VideoBulkProcessor:
    """Bulk processor for existing videos"""
    
    def __init__(self):
        self.db = None
        self.breakdown_service = DanceBreakdownService()
        self.processed_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        
    async def initialize(self):
        """Initialize database connection"""
        await Database.connect_to_mongo()
        self.db = Database.get_database()
        logger.info("🎬 Video Bulk Processor initialized")
    
    async def process_session_videos(self, limit: int = None, dry_run: bool = False) -> Dict[str, int]:
        """Process session videos that don't have processedVideoURL"""
        try:
            collection_name = Database.get_collection_name('dance_sessions')
            collection = self.db[collection_name]
            
            # Find sessions with videoURL but no processedVideoURL
            query = {
                "videoURL": {"$exists": True, "$ne": ""},
                "$or": [
                    {"processedVideoURL": {"$exists": False}},
                    {"processedVideoURL": {"$eq": ""}}
                ]
            }
            
            cursor = collection.find(query)
            if limit:
                cursor = cursor.limit(limit)
                
            sessions = await cursor.to_list(length=None)
            total_sessions = len(sessions)
            
            logger.info(f"📊 Found {total_sessions} session videos to process")
            
            if dry_run:
                logger.info("🔍 DRY RUN - No actual processing will be performed")
                for session in sessions:
                    logger.info(f"Would process session {session['_id']}: {session.get('videoURL')}")
                return {"found": total_sessions, "processed": 0, "failed": 0, "skipped": 0}
            
            # Process each session
            for i, session in enumerate(sessions, 1):
                try:
                    session_id = str(session['_id'])
                    user_id = str(session.get('userId', ''))
                    video_url = session.get('videoURL', '')
                    
                    logger.info(f"🎬 Processing session {i}/{total_sessions}: {session_id}")
                    
                    if not video_url:
                        logger.warning(f"⚠️ Skipping session {session_id}: No video URL")
                        self.skipped_count += 1
                        continue
                    
                    # Process video through mobile optimization pipeline
                    processed_url = await self._process_video(video_url, user_id, video_type="session")
                    
                    if processed_url:
                        # Update session with processed video URL
                        await collection.update_one(
                            {"_id": ObjectId(session_id)},
                            {"$set": {"processedVideoURL": processed_url}}
                        )
                        logger.info(f"✅ Session {session_id} processed successfully")
                        self.processed_count += 1
                    else:
                        logger.error(f"❌ Failed to process session {session_id}")
                        self.failed_count += 1
                        
                except Exception as e:
                    logger.error(f"❌ Error processing session {session.get('_id')}: {str(e)}")
                    self.failed_count += 1
                    continue
            
            return {
                "found": total_sessions,
                "processed": self.processed_count,
                "failed": self.failed_count,
                "skipped": self.skipped_count
            }
            
        except Exception as e:
            logger.error(f"❌ Error in process_session_videos: {str(e)}")
            raise
    
    async def process_challenge_videos(self, limit: int = None, dry_run: bool = False) -> Dict[str, int]:
        """Process challenge submission videos"""
        try:
            collection_name = Database.get_collection_name('challenge_submissions')
            collection = self.db[collection_name]
            
            # Find challenge submissions with video.url but no video.processed_url
            query = {
                "video.url": {"$exists": True, "$ne": ""},
                "$or": [
                    {"video.processed_url": {"$exists": False}},
                    {"video.processed_url": {"$eq": ""}}
                ]
            }
            
            cursor = collection.find(query)
            if limit:
                cursor = cursor.limit(limit)
                
            submissions = await cursor.to_list(length=None)
            total_submissions = len(submissions)
            
            logger.info(f"📊 Found {total_submissions} challenge videos to process")
            
            if dry_run:
                logger.info("🔍 DRY RUN - No actual processing will be performed")
                for submission in submissions:
                    video_url = submission.get('video', {}).get('url', '')
                    logger.info(f"Would process challenge submission {submission['_id']}: {video_url}")
                return {"found": total_submissions, "processed": 0, "failed": 0, "skipped": 0}
            
            # Process each submission
            for i, submission in enumerate(submissions, 1):
                try:
                    submission_id = str(submission['_id'])
                    user_id = str(submission.get('userId', ''))
                    video_data = submission.get('video', {})
                    video_url = video_data.get('url', '')
                    
                    logger.info(f"🎬 Processing challenge submission {i}/{total_submissions}: {submission_id}")
                    
                    if not video_url:
                        logger.warning(f"⚠️ Skipping submission {submission_id}: No video URL")
                        self.skipped_count += 1
                        continue
                    
                    # Process video through mobile optimization pipeline
                    processed_url = await self._process_video(video_url, user_id, video_type="challenge")
                    
                    if processed_url:
                        # Update submission with processed video URL
                        await collection.update_one(
                            {"_id": ObjectId(submission_id)},
                            {"$set": {"video.processed_url": processed_url}}
                        )
                        logger.info(f"✅ Challenge submission {submission_id} processed successfully")
                        self.processed_count += 1
                    else:
                        logger.error(f"❌ Failed to process challenge submission {submission_id}")
                        self.failed_count += 1
                        
                except Exception as e:
                    logger.error(f"❌ Error processing challenge submission {submission.get('_id')}: {str(e)}")
                    self.failed_count += 1
                    continue
            
            return {
                "found": total_submissions,
                "processed": self.processed_count,
                "failed": self.failed_count,
                "skipped": self.skipped_count
            }
            
        except Exception as e:
            logger.error(f"❌ Error in process_challenge_videos: {str(e)}")
            raise
    
    async def _process_video(self, video_url: str, user_id: str, video_type: str = "user") -> str:
        """Process a single video through the mobile optimization pipeline"""
        try:
            logger.info(f"🎬 Processing {video_type} video: {video_url}")
            
            # Download video from S3
            temp_video_path = await self.breakdown_service.download_from_s3(video_url)
            
            if not temp_video_path:
                logger.error(f"❌ Failed to download video: {video_url}")
                return None
            
            try:
                # Process video through resizing middleware (same as breakdown videos)
                processed_video_path = await video_resizing_middleware.process_video_file(
                    temp_video_path, 
                    cleanup_original=False
                )
                
                # Upload processed video back to S3 with mobile-optimized path
                processed_video_url = await self.breakdown_service.upload_video_to_s3(
                    processed_video_path, 
                    user_id, 
                    video_url
                )
                
                logger.info(f"✅ Video processed successfully: {processed_video_url}")
                return processed_video_url
                
            finally:
                # Clean up temporary files
                try:
                    if temp_video_path and os.path.exists(temp_video_path):
                        os.remove(temp_video_path)
                    if processed_video_path and processed_video_path != temp_video_path and os.path.exists(processed_video_path):
                        os.remove(processed_video_path)
                except Exception as cleanup_error:
                    logger.warning(f"⚠️ Failed to cleanup temp files: {cleanup_error}")
                    
        except Exception as e:
            logger.error(f"❌ Error processing video {video_url}: {str(e)}")
            return None
    
    async def generate_report(self, results: Dict[str, Any]):
        """Generate processing report"""
        logger.info("📊 PROCESSING REPORT")
        logger.info("=" * 50)
        
        for video_type, stats in results.items():
            logger.info(f"{video_type.upper()} VIDEOS:")
            logger.info(f"  Found: {stats['found']}")
            logger.info(f"  Processed: {stats['processed']}")
            logger.info(f"  Failed: {stats['failed']}")
            logger.info(f"  Skipped: {stats['skipped']}")
            logger.info("-" * 30)
        
        total_found = sum(stats['found'] for stats in results.values())
        total_processed = sum(stats['processed'] for stats in results.values())
        total_failed = sum(stats['failed'] for stats in results.values())
        total_skipped = sum(stats['skipped'] for stats in results.values())
        
        logger.info("TOTAL SUMMARY:")
        logger.info(f"  Found: {total_found}")
        logger.info(f"  Processed: {total_processed}")
        logger.info(f"  Failed: {total_failed}")
        logger.info(f"  Skipped: {total_skipped}")
        
        success_rate = (total_processed / total_found * 100) if total_found > 0 else 0
        logger.info(f"  Success Rate: {success_rate:.1f}%")
        logger.info("=" * 50)

async def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bulk process existing videos for mobile compatibility')
    parser.add_argument('--type', choices=['sessions', 'challenges', 'all'], default='all',
                       help='Type of videos to process (default: all)')
    parser.add_argument('--limit', type=int, help='Limit number of videos to process')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without actually processing')
    
    args = parser.parse_args()
    
    processor = VideoBulkProcessor()
    await processor.initialize()
    
    results = {}
    
    try:
        logger.info(f"🚀 Starting bulk video processing (type: {args.type})")
        
        if args.type in ['sessions', 'all']:
            logger.info("🎬 Processing session videos...")
            results['sessions'] = await processor.process_session_videos(
                limit=args.limit, 
                dry_run=args.dry_run
            )
        
        if args.type in ['challenges', 'all']:
            logger.info("🏆 Processing challenge videos...")
            results['challenges'] = await processor.process_challenge_videos(
                limit=args.limit, 
                dry_run=args.dry_run
            )
        
        await processor.generate_report(results)
        
    except Exception as e:
        logger.error(f"❌ Fatal error in bulk processing: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)