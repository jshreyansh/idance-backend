#!/usr/bin/env python3
"""
Background Video Processing Service for Session Videos
Uses the same proven processing pipeline as dance breakdowns
"""

import asyncio
import logging
import os
import tempfile
import subprocess
import hashlib
import boto3
import requests
from datetime import datetime
from typing import Optional
from botocore.exceptions import ClientError

from services.video_processing.middleware import video_resizing_middleware
from infra.mongo import Database
from bson import ObjectId

logger = logging.getLogger(__name__)

class BackgroundVideoProcessor:
    """Background service for processing session videos using the same pipeline as dance breakdowns"""
    
    def __init__(self):
        self.s3_client = None
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'idanceshreyansh')
        self.bucket_url = os.getenv('S3_BUCKET_URL', f'https://{self.bucket_name}.s3.ap-south-1.amazonaws.com')
    
    def _get_s3_client(self):
        """Initialize S3 client (same as breakdown service)"""
        if not self.s3_client:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION', 'ap-south-1')
            )
        return self.s3_client
    
    def _extract_file_key_from_url(self, s3_url: str) -> str:
        """Extract S3 file key from URL (same logic as breakdown service)"""
        try:
            # Handle different S3 URL formats
            if 'amazonaws.com/' in s3_url:
                # Extract everything after the domain and first slash
                parts = s3_url.split('amazonaws.com/')
                if len(parts) > 1:
                    return parts[1]
            
            # Fallback: try to extract from the end of URL
            if '/' in s3_url:
                # Get everything after the last occurrence of the bucket name
                if self.bucket_name in s3_url:
                    parts = s3_url.split(self.bucket_name + '/')
                    if len(parts) > 1:
                        return parts[1]
            
            raise Exception(f"Could not extract file key from URL: {s3_url}")
            
        except Exception as e:
            logger.error(f"❌ Error extracting file key from URL {s3_url}: {str(e)}")
            raise
    
    async def download_from_s3(self, s3_url: str) -> Optional[str]:
        """Download video from S3 to temporary file (same as breakdown service)"""
        try:
            logger.info(f"📥 Downloading session video from S3: {s3_url}")
            
            # Extract file key from S3 URL
            file_key = self._extract_file_key_from_url(s3_url)
            logger.info(f"📁 Extracted file key: {file_key}")
            
            # Download to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            temp_path = temp_file.name
            temp_file.close()
            
            # Use S3 client to download
            s3_client = self._get_s3_client()
            
            logger.info(f"📦 Downloading from bucket: {self.bucket_name}, key: {file_key}")
            s3_client.download_file(self.bucket_name, file_key, temp_path)
            
            logger.info(f"✅ Successfully downloaded session video: {s3_url} -> {temp_path}")
            
            # Validate downloaded file
            file_size = os.path.getsize(temp_path)
            logger.info(f"📁 Downloaded file size: {file_size} bytes")
            
            if file_size < 1000:  # Less than 1KB is suspicious
                raise Exception(f"Downloaded file is too small ({file_size} bytes)")
            
            # Validate it's a video using ffprobe
            try:
                cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', temp_path]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                logger.info("✅ Video file validation successful")
            except subprocess.CalledProcessError as e:
                logger.warning(f"⚠️ Video validation failed but continuing: {str(e)}")
            
            return temp_path
            
        except Exception as e:
            logger.error(f"❌ Failed to download video from S3: {str(e)}")
            return None
    
    async def upload_processed_video_to_s3(self, video_path: str, user_id: str, session_id: str, original_url: str) -> str:
        """Upload processed video to S3 (adapted from breakdown service)"""
        try:
            logger.info(f"📤 Uploading processed session video for user: {user_id}, session: {session_id}")
            
            # Process video through resizing middleware first (same as breakdowns)
            processed_video_path = await video_resizing_middleware.process_video_file(video_path, cleanup_original=False)
            
            # Generate unique file key for processed session video
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            url_hash = hashlib.md5(original_url.encode()).hexdigest()[:8]
            file_key = f"sessions/{user_id}/{session_id}/processed_{timestamp}_{url_hash}.mp4"
            
            # Upload processed video to S3
            s3_client = self._get_s3_client()
            s3_client.upload_file(processed_video_path, self.bucket_name, file_key)
            
            # Generate public URL
            processed_video_url = f"{self.bucket_url}/{file_key}"
            
            logger.info(f"✅ Processed session video uploaded to S3: {processed_video_url}")
            return processed_video_url
            
        except Exception as e:
            logger.error(f"❌ Failed to upload processed session video: {str(e)}")
            # Return original URL as fallback (same as breakdown service)
            return original_url
    
    async def queue_session_video_processing(
        self, 
        session_id: str, 
        video_url: str, 
        user_id: str
    ):
        """Queue session video for background processing"""
        logger.info(f"🎬 Queuing session video processing: session={session_id}, user={user_id}")
        
        # For now, process immediately in background task
        # Later can be replaced with proper job queue (Celery/Redis)
        asyncio.create_task(self._process_session_video_background(
            session_id, video_url, user_id
        ))
        
        logger.info(f"✅ Session video processing queued: {session_id}")
    
    async def queue_challenge_video_processing(
        self, 
        submission_id: str, 
        video_url: str, 
        user_id: str
    ):
        """Queue challenge submission video for background processing"""
        logger.info(f"🏆 Queuing challenge video processing: submission={submission_id}, user={user_id}")
        
        # For now, process immediately in background task
        # Later can be replaced with proper job queue (Celery/Redis)
        asyncio.create_task(self._process_challenge_video_background(
            submission_id, video_url, user_id
        ))
        
        logger.info(f"✅ Challenge video processing queued: {submission_id}")
    
    async def queue_demo_video_processing(
        self, 
        challenge_id: str, 
        video_url: str, 
        user_id: str
    ):
        """Queue challenge demo video for background processing"""
        logger.info(f"🎯 Queuing demo video processing: challenge={challenge_id}, user={user_id}")
        
        # For now, process immediately in background task
        # Later can be replaced with proper job queue (Celery/Redis)
        asyncio.create_task(self._process_demo_video_background(
            challenge_id, video_url, user_id
        ))
        
        logger.info(f"✅ Demo video processing queued: {challenge_id}")
    
    async def _process_session_video_background(
        self, 
        session_id: str, 
        video_url: str, 
        user_id: str
    ):
        """Process session video in background using the same pipeline as breakdowns"""
        temp_video_path = None
        processed_video_path = None
        
        try:
            logger.info(f"🎬 Starting background processing for session: {session_id}")
            logger.info(f"📹 Video URL: {video_url}")
            
            # Step 1: Download video from S3 (same as breakdowns)
            temp_video_path = await self.download_from_s3(video_url)
            
            if not temp_video_path:
                logger.error(f"❌ Failed to download session video: {video_url}")
                return
            
            # Step 2: Process through resizing middleware and upload (same as breakdowns)
            processed_video_url = await self.upload_processed_video_to_s3(
                temp_video_path, user_id, session_id, video_url
            )
            
            # Step 3: Update session document with processed URL
            await self._update_session_with_processed_url(session_id, processed_video_url)
            
            logger.info(f"✅ Session video processing completed: {session_id}")
            logger.info(f"🎯 Processed URL: {processed_video_url}")
            
        except Exception as e:
            logger.error(f"❌ Error processing session video {session_id}: {str(e)}")
            
        finally:
            # Clean up temporary files
            self._cleanup_temp_files([temp_video_path, processed_video_path])
    
    async def _process_challenge_video_background(
        self, 
        submission_id: str, 
        video_url: str, 
        user_id: str
    ):
        """Process challenge submission video in background using the same pipeline as sessions"""
        temp_video_path = None
        processed_video_path = None
        
        try:
            logger.info(f"🏆 Starting background processing for challenge submission: {submission_id}")
            logger.info(f"📹 Video URL: {video_url}")
            
            # Step 1: Download video from S3 (same as sessions)
            temp_video_path = await self.download_from_s3(video_url)
            
            if not temp_video_path:
                logger.error(f"❌ Failed to download challenge video: {video_url}")
                return
            
            # Step 2: Process through resizing middleware and upload (same as sessions)
            processed_video_url = await self.upload_processed_challenge_video_to_s3(
                temp_video_path, user_id, submission_id, video_url
            )
            
            # Step 3: Update challenge submission document with processed URL
            await self._update_challenge_with_processed_url(submission_id, processed_video_url)
            
            logger.info(f"✅ Challenge video processing completed: {submission_id}")
            logger.info(f"🎯 Processed URL: {processed_video_url}")
            
        except Exception as e:
            logger.error(f"❌ Error processing challenge video {submission_id}: {str(e)}")
            
        finally:
            # Clean up temporary files
            self._cleanup_temp_files([temp_video_path, processed_video_path])
    
    async def _process_demo_video_background(
        self, 
        challenge_id: str, 
        video_url: str, 
        user_id: str
    ):
        """Process challenge demo video in background using the same pipeline"""
        temp_video_path = None
        processed_video_path = None
        
        try:
            logger.info(f"🎯 Starting background processing for demo video: {challenge_id}")
            logger.info(f"📹 Video URL: {video_url}")
            
            # Step 1: Download video from S3 (enhanced for temporary bucket approach)
            temp_video_path = await self.download_demo_video_from_s3(video_url)
            
            if not temp_video_path:
                logger.error(f"❌ Failed to download demo video: {video_url}")
                return
            
            # Step 2: Process through resizing middleware and upload
            processed_video_url = await self.upload_processed_demo_video_to_s3(
                temp_video_path, user_id, challenge_id, video_url
            )
            
            # Step 3: Update challenge document with processed demo URL
            await self._update_challenge_demo_with_processed_url(challenge_id, processed_video_url)
            
            logger.info(f"✅ Demo video processing completed: {challenge_id}")
            logger.info(f"🎯 Processed URL: {processed_video_url}")
            
        except Exception as e:
            logger.error(f"❌ Error processing demo video {challenge_id}: {str(e)}")
            
        finally:
            # Clean up temporary files
            self._cleanup_temp_files([temp_video_path, processed_video_path])
    
    async def download_demo_video_from_s3(self, video_url: str) -> Optional[str]:
        """Download demo video from S3 with enhanced error handling for temporary bucket approach"""
        try:
            logger.info(f"📥 Downloading demo video from S3: {video_url}")
            
            # Extract file key from URL
            file_key = self._extract_file_key_from_url(video_url)
            if not file_key:
                logger.error(f"❌ Could not extract file key from URL: {video_url}")
                return None
            
            logger.info(f"📁 Extracted file key: {file_key}")
            
            # Try multiple download approaches
            temp_video_path = None
            
            # Approach 1: Try direct S3 download (for same bucket)
            try:
                temp_video_path = await self._download_from_s3_direct(file_key)
                if temp_video_path:
                    logger.info(f"✅ Demo video downloaded successfully via direct S3: {temp_video_path}")
                    return temp_video_path
            except Exception as e:
                logger.warning(f"⚠️ Direct S3 download failed: {str(e)}")
            
            # Approach 2: Try HTTP download (for public URLs)
            try:
                temp_video_path = await self._download_via_http(video_url)
                if temp_video_path:
                    logger.info(f"✅ Demo video downloaded successfully via HTTP: {temp_video_path}")
                    return temp_video_path
            except Exception as e:
                logger.warning(f"⚠️ HTTP download failed: {str(e)}")
            
            logger.error(f"❌ All download methods failed for demo video: {video_url}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error in demo video download: {str(e)}")
            return None
    
    async def _download_from_s3_direct(self, file_key: str) -> Optional[str]:
        """Download file directly from S3 using boto3"""
        try:
            import tempfile
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            temp_path = temp_file.name
            temp_file.close()
            
            # Download from S3
            s3_client = self._get_s3_client()
            s3_client.download_file(self.bucket_name, file_key, temp_path)
            
            # Verify file exists and has content
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                logger.info(f"📦 Downloaded from bucket: {self.bucket_name}, key: {file_key}")
                return temp_path
            else:
                logger.error(f"❌ Downloaded file is empty or missing: {temp_path}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to download from S3: {str(e)}")
            return None
    
    async def _download_via_http(self, video_url: str) -> Optional[str]:
        """Download video via HTTP requests"""
        try:
            import tempfile
            import requests
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            temp_path = temp_file.name
            temp_file.close()
            
            # Download via HTTP
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verify file exists and has content
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                logger.info(f"📥 Downloaded via HTTP: {video_url}")
                return temp_path
            else:
                logger.error(f"❌ Downloaded file is empty or missing: {temp_path}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to download via HTTP: {str(e)}")
            return None
    
    async def upload_processed_challenge_video_to_s3(self, video_path: str, user_id: str, submission_id: str, original_url: str) -> str:
        """Upload processed challenge video to S3 (adapted from session processing)"""
        try:
            logger.info(f"📤 Uploading processed challenge video for user: {user_id}, submission: {submission_id}")
            
            # Process video through resizing middleware first (same as sessions)
            processed_video_path = await video_resizing_middleware.process_video_file(video_path, cleanup_original=False)
            
            # Generate unique file key for processed challenge video
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            url_hash = hashlib.md5(original_url.encode()).hexdigest()[:8]
            file_key = f"challenges/{user_id}/submissions/{submission_id}/processed_{timestamp}_{url_hash}.mp4"
            
            # Upload processed video to S3
            s3_client = self._get_s3_client()
            s3_client.upload_file(processed_video_path, self.bucket_name, file_key)
            
            # Generate public URL
            processed_video_url = f"{self.bucket_url}/{file_key}"
            
            logger.info(f"✅ Processed challenge video uploaded to S3: {processed_video_url}")
            return processed_video_url
            
        except Exception as e:
            logger.error(f"❌ Failed to upload processed challenge video: {str(e)}")
            # Return original URL as fallback
            return original_url
    
    async def upload_processed_demo_video_to_s3(self, video_path: str, user_id: str, challenge_id: str, original_url: str) -> str:
        """Upload processed demo video to S3"""
        try:
            logger.info(f"📤 Uploading processed demo video for challenge: {challenge_id}")
            
            # Process video through resizing middleware first
            processed_video_path = await video_resizing_middleware.process_video_file(video_path, cleanup_original=False)
            
            # Generate unique file key for processed demo video
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            url_hash = hashlib.md5(original_url.encode()).hexdigest()[:8]
            file_key = f"challenges/{challenge_id}/demo/processed_{timestamp}_{url_hash}.mp4"
            
            # Upload processed video to S3
            s3_client = self._get_s3_client()
            s3_client.upload_file(processed_video_path, self.bucket_name, file_key)
            
            # Generate public URL
            processed_video_url = f"{self.bucket_url}/{file_key}"
            
            logger.info(f"✅ Processed demo video uploaded to S3: {processed_video_url}")
            return processed_video_url
            
        except Exception as e:
            logger.error(f"❌ Failed to upload processed demo video: {str(e)}")
            # Return original URL as fallback
            return original_url
    
    async def _update_session_with_processed_url(
        self, 
        session_id: str, 
        processed_url: str
    ):
        """Update session document with processed video URL"""
        try:
            db = Database.get_database()
            collection_name = Database.get_collection_name('dance_sessions')
            
            result = await db[collection_name].update_one(
                {"_id": ObjectId(session_id)},
                {"$set": {"processedVideoURL": processed_url}}
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Updated session {session_id} with processed URL")
            else:
                logger.warning(f"⚠️ No session found to update: {session_id}")
                
        except Exception as e:
            logger.error(f"❌ Failed to update session {session_id}: {str(e)}")
            raise
    
    async def _update_challenge_with_processed_url(
        self, 
        submission_id: str, 
        processed_url: str
    ):
        """Update challenge submission document with processed video URL"""
        try:
            db = Database.get_database()
            collection_name = Database.get_collection_name('challenge_submissions')
            
            result = await db[collection_name].update_one(
                {"_id": ObjectId(submission_id)},
                {"$set": {"video.processed_url": processed_url}}
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Updated challenge submission {submission_id} with processed URL")
            else:
                logger.warning(f"⚠️ No challenge submission found to update: {submission_id}")
                
        except Exception as e:
            logger.error(f"❌ Failed to update challenge submission {submission_id}: {str(e)}")
            raise
    
    async def _update_challenge_demo_with_processed_url(
        self, 
        challenge_id: str, 
        processed_url: str
    ):
        """Update challenge document with processed demo video URL"""
        try:
            db = Database.get_database()
            collection_name = Database.get_collection_name('challenges')
            
            result = await db[collection_name].update_one(
                {"_id": ObjectId(challenge_id)},
                {"$set": {"processedDemoVideoURL": processed_url}}
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Updated challenge {challenge_id} with processed demo URL")
            else:
                logger.warning(f"⚠️ No challenge found to update: {challenge_id}")
                
        except Exception as e:
            logger.error(f"❌ Failed to update challenge {challenge_id}: {str(e)}")
            raise
    
    def _cleanup_temp_files(self, file_paths: list):
        """Clean up temporary files"""
        for file_path in file_paths:
            try:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"🧹 Cleaned up temp file: {file_path}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to cleanup {file_path}: {e}")

# Global instance
background_video_processor = BackgroundVideoProcessor()