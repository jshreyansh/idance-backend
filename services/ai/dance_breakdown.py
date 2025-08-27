#!/usr/bin/env python3
"""
Dance Breakdown Service for YouTube/Instagram URL processing
"""

import asyncio
import json
import logging
import os
import tempfile
import yt_dlp
import subprocess
import numpy as np
import librosa
import cv2
import mediapipe as mp
import ruptures as rpt
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from openai import AsyncOpenAI
from dotenv import load_dotenv
from fastapi import HTTPException

from services.ai.models import (
    DanceBreakdownRequest, 
    DanceBreakdownResponse, 
    DanceStep,
    DanceBreakdownStatus
)
from services.ai.movement_analysis import analyze_movement_enhanced
from infra.mongo import Database
# Environment-aware collection names
user_stats_collection = Database.get_collection_name('user_stats')
dance_breakdowns_collection = Database.get_collection_name('dance_breakdowns')

from bson import ObjectId

# Load environment variables
load_dotenv()

# Configure logging to reduce MediaPipe warnings
logging.basicConfig(level=logging.INFO)
logging.getLogger('mediapipe').setLevel(logging.ERROR)
logging.getLogger('absl').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

class DanceBreakdownService:
    """Service for processing dance videos from URLs and generating step-by-step breakdowns"""
    
    def __init__(self):
        # Initialize OpenAI client with proper configuration
        self.openai_client = None
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                self.openai_client = AsyncOpenAI(api_key=api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {str(e)}")
                self.openai_client = None
        else:
            logger.warning("OpenAI API key not found. Dance breakdown will use manual mode only.")
        
        self.mp_pose = mp.solutions.pose.Pose(static_image_mode=False)
        self.breakdown_queue = {}  # In-memory queue for tracking processing status
        self.db = None
        
    def format_timestamp(self, seconds: float) -> str:
        """Format seconds into MM:SS.mmm format"""
        minutes = int(seconds // 60)
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:06.3f}"
    
    def timestamp_to_seconds(self, ts: str) -> float:
        """Convert timestamp string to seconds"""
        try:
            parts = ts.split(':')
            if len(parts) == 2:
                minutes = int(parts[0])
                if '.' in parts[1]:
                    secs, millis = parts[1].split('.')
                    return minutes * 60 + int(secs) + int(millis) / 1000
                else:
                    return minutes * 60 + int(parts[1])
            return float(ts)
        except Exception:
            return 0.0
    
    def _clean_youtube_url(self, url: str) -> str:
        """Clean YouTube URL to remove playlist and other parameters"""
        import re
        
        # Extract video ID from various YouTube URL formats
        video_id_patterns = [
            r'(?:v=|/)([0-9A-Za-z_-]{11}).*',  # Standard and short URLs
            r'(?:embed/)([0-9A-Za-z_-]{11})',   # Embed URLs
            r'(?:shorts/)([0-9A-Za-z_-]{11})',  # YouTube Shorts
        ]
        
        for pattern in video_id_patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                # Return clean URL with just the video ID
                if 'shorts/' in url:
                    return f"https://www.youtube.com/shorts/{video_id}"
                else:
                    return f"https://www.youtube.com/watch?v={video_id}"
        
        # If no pattern matches, return original URL
        logger.warning(f"Could not extract video ID from URL: {url}")
        return url
    
    async def download_video(self, url: str, cookies_path: Optional[str] = None) -> str:
        """Download video from URL with multiple fallback strategies"""
        temp_file = tempfile.mktemp(suffix=".mp4")
        
        # Handle different URL types
        if "instagram.com" in url:
            # For Instagram URLs, use the original URL directly
            clean_url = url
            logger.info(f"Processing Instagram URL: {clean_url}")
        else:
            # For YouTube URLs, clean to extract just the video ID
            clean_url = self._clean_youtube_url(url)
            logger.info(f"Processing YouTube URL: {clean_url}")
        
        logger.info(f"Attempting to download: {clean_url}")
        
        # Multiple download strategies to try
        strategies = []
        
        if "instagram.com" in url:
            # Instagram-specific strategies
            strategies = [
                # Strategy 1: Instagram with cookies (most reliable)
                {
                    'name': 'instagram_with_cookies',
                    'opts': {
                        'format': 'best[ext=mp4]/best',
                        'outtmpl': temp_file,
                        'cookiefile': cookies_path if cookies_path and os.path.exists(cookies_path) else None,
                        'quiet': True,
                        'noplaylist': True,
                    }
                },
                # Strategy 2: Instagram without cookies
                {
                    'name': 'instagram_basic',
                    'opts': {
                        'format': 'best[ext=mp4]/best',
                        'outtmpl': temp_file,
                        'quiet': True,
                        'noplaylist': True,
                    }
                }
            ]
        else:
            # YouTube-specific strategies
            strategies = [
                # Strategy 1: iOS client (most reliable)
                {
                    'name': 'ios_client',
                    'opts': {
                        'format': 'best[ext=mp4][height<=720]/best[ext=mp4]/best',
                        'outtmpl': temp_file,
                        'cookiefile': cookies_path if cookies_path and os.path.exists(cookies_path) else None,
                        'quiet': True,
                        'noplaylist': True,  # Crucial: Don't download playlists
                        'extractor_args': {
                            'youtube': {
                                'player_client': ['ios'],
                            }
                        }
                    }
                },
                # Strategy 2: Android client  
                {
                    'name': 'android_client',
                    'opts': {
                        'format': 'best[ext=mp4]/best',
                        'outtmpl': temp_file,
                        'cookiefile': cookies_path if cookies_path and os.path.exists(cookies_path) else None,
                        'quiet': True,
                        'noplaylist': True,
                        'extractor_args': {
                            'youtube': {
                                'player_client': ['android'],
                            }
                        }
                    }
                },
                # Strategy 3: Basic download (lowest quality)
                {
                    'name': 'basic_low_quality',
                    'opts': {
                        'format': 'worst[ext=mp4]/worst',
                        'outtmpl': temp_file,
                        'cookiefile': cookies_path if cookies_path and os.path.exists(cookies_path) else None,
                        'quiet': True,
                        'noplaylist': True,
                    }
                }
            ]
        
        for i, strategy in enumerate(strategies):
            try:
                logger.info(f"Trying strategy {i+1}: {strategy['name']}")
                
                with yt_dlp.YoutubeDL(strategy['opts']) as ydl:
                    ydl.download([clean_url])
                
                # Verify the file was downloaded
                if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                    file_size = os.path.getsize(temp_file) / (1024 * 1024)  # MB
                    logger.info(f"✅ Video downloaded successfully with {strategy['name']}: {file_size:.1f}MB")
                    return temp_file
                else:
                    logger.warning(f"Strategy {strategy['name']} failed: file not created or empty")
                    continue
                    
            except Exception as e:
                logger.warning(f"Strategy {strategy['name']} failed: {str(e)}")
                # Clean up any partial files before trying next strategy
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                continue
        
        # If all strategies failed, provide helpful error message
        if "instagram.com" in url:
            error_msg = f"All download strategies failed for Instagram URL {url}. This video may be:"
            error_msg += "\n- Private or deleted"
            error_msg += "\n- Age-restricted requiring sign-in"
            error_msg += "\n- Protected by Instagram's anti-bot measures"
            error_msg += "\n- Requires authentication (check cookies_instagram.txt)"
            error_msg += "\nTry using a different Instagram video URL."
        else:
            error_msg = f"All download strategies failed for YouTube URL {url}. This video may be:"
            error_msg += "\n- Geo-restricted or region-locked"
            error_msg += "\n- Age-restricted requiring sign-in"
            error_msg += "\n- Private or deleted"
            error_msg += "\n- Protected by YouTube's anti-bot measures"
            error_msg += "\nTry using a different YouTube video URL."
        
        logger.error(error_msg)
        raise Exception(error_msg)
    
    async def upload_video_to_s3(self, video_path: str, user_id: str, original_url: str) -> str:
        """Upload downloaded video to S3 and return playable URL"""
        try:
            import boto3
            from botocore.exceptions import ClientError
            import hashlib
            import os
            
            # Process video through resizing middleware first
            from services.video_processing.middleware import video_resizing_middleware
            processed_video_path = await video_resizing_middleware.process_video_file(video_path, cleanup_original=False)
            
            # Initialize S3 client
            s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION', 'ap-south-1')
            )
            
            # Generate unique file key
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            url_hash = hashlib.md5(original_url.encode()).hexdigest()[:8]
            file_key = f"dance-breakdowns/{user_id}/{timestamp}_{url_hash}.mp4"
            
            # Upload processed video to S3
            bucket_name = os.getenv('S3_BUCKET_NAME', 'idanceshreyansh')
            s3_client.upload_file(processed_video_path, bucket_name, file_key)
            
            # Generate public URL
            bucket_url = os.getenv('S3_BUCKET_URL', f'https://{bucket_name}.s3.ap-south-1.amazonaws.com')
            video_url = f"{bucket_url}/{file_key}"
            
            logger.info(f"✅ Video uploaded to S3 with resizing: {video_url}")
            return video_url
            
        except Exception as e:
            logger.error(f"❌ Failed to upload video to S3: {str(e)}")
            # Return original URL as fallback
            return original_url
    
    async def download_from_s3(self, s3_url: str) -> str:
        """Download video from S3 to temporary file"""
        try:
            logger.info(f"📥 Downloading video from S3: {s3_url}")
            
            # Extract file key from S3 URL
            file_key = self._extract_file_key_from_url(s3_url)
            logger.info(f"📁 Extracted file key: {file_key}")
            
            # Download to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            temp_path = temp_file.name
            temp_file.close()
            
            # Use boto3 to download
            import boto3
            s3_client = boto3.client('s3')
            bucket_name = os.getenv('S3_BUCKET_NAME')
            
            if not bucket_name:
                raise Exception("S3_BUCKET_NAME environment variable not set")
            
            logger.info(f"📦 Downloading from bucket: {bucket_name}, key: {file_key}")
            s3_client.download_file(bucket_name, file_key, temp_path)
            
            logger.info(f"✅ Successfully downloaded video from S3: {s3_url} -> {temp_path}")
            
            # Validate that the downloaded file is actually a video
            file_size = os.path.getsize(temp_path)
            logger.info(f"📁 Downloaded file size: {file_size} bytes")
            
            if file_size < 1000:  # Less than 1KB is suspicious
                raise Exception(f"Downloaded file is too small ({file_size} bytes) - likely not a valid video file")
            
            # Try to get video info using ffprobe
            try:
                cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', temp_path]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                video_info = result.stdout
                logger.info(f"✅ Video file validation successful: {temp_path}")
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Downloaded file is not a valid video: {e.stderr}")
                raise Exception(f"Downloaded file is not a valid video file: {e.stderr}")
            
            return temp_path
            
        except Exception as e:
            logger.error(f"❌ Error downloading from S3: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to download video from S3: {str(e)}")

    def _extract_file_key_from_url(self, s3_url: str) -> str:
        """Extract S3 file key from URL"""
        try:
            # Parse URL and extract path
            from urllib.parse import urlparse
            parsed = urlparse(s3_url)
            file_key = parsed.path.lstrip('/')
            
            # Remove bucket name if it's in the path
            bucket_name = os.getenv('S3_BUCKET_NAME', '')
            if bucket_name and file_key.startswith(bucket_name + '/'):
                file_key = file_key[len(bucket_name) + 1:]
            
            logger.info(f"🔍 Extracted file key: {file_key} from URL: {s3_url}")
            return file_key
            
        except Exception as e:
            logger.error(f"❌ Error extracting file key from URL: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid S3 URL format")

    def _get_cookies_path(self, url: str) -> Optional[str]:
        """Determine the appropriate cookies file path based on URL."""
        if "instagram.com" in url:
            return 'cookies_instagram.txt'
        elif "youtube.com" in url or "youtu.be" in url:
            return 'cookies_youtube.txt'
        else:
            return None
    
    def _get_db(self):
        """Get database connection"""
        if self.db is None:
            self.db = Database.get_database()
        return self.db
    
    async def save_breakdown_to_db(self, user_id: str, request: DanceBreakdownRequest, response: DanceBreakdownResponse, thumbnail_url: str = "") -> str:
        """Save dance breakdown to database and update user stats"""
        try:
            db = self._get_db()
            
            breakdown_doc = {
                "userId": ObjectId(user_id),
                "videoUrl": request.video_url,
                "playableVideoUrl": response.playable_video_url,
                "thumbnailUrl": thumbnail_url,  # Add thumbnail URL
                "title": response.title,
                "mode": request.mode,
                "targetDifficulty": request.target_difficulty,
                "duration": response.duration,
                "bpm": response.bpm,
                "difficultyLevel": response.difficulty_level,
                "totalSteps": response.total_steps,
                "routineAnalysis": response.routine_analysis,
                "steps": [step.dict() for step in response.steps],
                "outlineUrl": response.outline_url,
                "success": response.success,
                "errorMessage": response.error_message,
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            }
            
            result = await db[dance_breakdowns_collection].insert_one(breakdown_doc)
            breakdown_id = str(result.inserted_id)
            
            # Update user stats for breakdown
            if response.success:
                # Update user stats and streaks using unified function
                from services.user.service import update_user_streaks_and_activity_unified
                await update_user_streaks_and_activity_unified(db, user_id, "breakdown")
                
                # Update breakdown-specific stats
                await self._update_user_stats_from_breakdown(db, user_id, response)
            
            logger.info(f"✅ Breakdown saved to database with ID: {breakdown_id}")
            return breakdown_id
            
        except Exception as e:
            logger.error(f"❌ Failed to save breakdown to database: {str(e)}")
            raise
    
    async def _update_user_stats_from_breakdown(self, db, user_id: str, response: DanceBreakdownResponse):
        """Update user stats based on successful dance breakdown"""
        try:
            # Calculate calories based on duration (similar to sessions)
            duration_minutes = int(response.duration / 60) if response.duration > 0 else 1
            calories_burned = int(duration_minutes * 4)  # Example: 4 calories per minute for analysis
            
            # Get current date for weekly activity
            today = datetime.utcnow().strftime('%Y-%m-%d')
            
            # Get current user stats
            user_stats = await db[user_stats_collection].find_one({'_id': ObjectId(user_id)}) or {}
            weekly_activity = user_stats.get('weeklyActivity', [])
            
            # Update weekly activity for today
            today_found = False
            for activity in weekly_activity:
                if activity['date'] == today:
                    # Ensure sessionsCount exists (for backward compatibility)
                    if 'sessionsCount' not in activity:
                        activity['sessionsCount'] = 0
                    activity['sessionsCount'] += 1
                    today_found = True
                    break
            
            if not today_found:
                weekly_activity.append({'date': today, 'sessionsCount': 1})
            
            # Keep only last 7 days
            today_date = datetime.strptime(today, '%Y-%m-%d').date()
            seven_days_ago = today_date - timedelta(days=6)
            weekly_activity = [
                activity for activity in weekly_activity 
                if datetime.strptime(activity['date'], '%Y-%m-%d').date() >= seven_days_ago
            ]
            
            # Update user stats
            await db[user_stats_collection].update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$inc": {
                        "totalKcal": calories_burned,
                        "totalTimeMinutes": duration_minutes,
                        "totalBreakdowns": 1
                    },
                    "$set": {
                        "updatedAt": datetime.utcnow(),
                        "mostPlayedStyle": "analysis",
                        "weeklyActivity": weekly_activity
                    }
                },
                upsert=True
            )
            
            logger.info(f"✅ Updated user {user_id} stats for dance breakdown.")
            
        except Exception as e:
            logger.error(f"❌ Error updating user stats from breakdown: {e}")
            # Don't raise - we don't want to fail the breakdown if stats update fails
    
    async def get_user_breakdowns(self, user_id: str, limit: int = 20, skip: int = 0) -> List[Dict]:
        """Get user's dance breakdown history"""
        try:
            db = self._get_db()
            
            cursor = db[dance_breakdowns_collection].find(
                {"userId": ObjectId(user_id)},
                {
                    "videoUrl": 1,
                    "title": 1, 
                    "mode": 1,
                    "targetDifficulty": 1,
                    "duration": 1,
                    "bpm": 1,
                    "difficultyLevel": 1,
                    "totalSteps": 1,
                    "success": 1,
                    "createdAt": 1
                }
            ).sort("createdAt", -1).skip(skip).limit(limit)
            
            breakdowns = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string
            for breakdown in breakdowns:
                breakdown['_id'] = str(breakdown['_id'])
                breakdown['userId'] = str(breakdown['userId'])
            
            logger.info(f"📊 Retrieved {len(breakdowns)} breakdowns for user {user_id}")
            return breakdowns
            
        except Exception as e:
            logger.error(f"❌ Failed to get user breakdowns: {str(e)}")
            raise
    
    async def get_breakdown_by_id(self, breakdown_id: str, user_id: str) -> Optional[Dict]:
        """Get specific breakdown by ID (user must own it)"""
        try:
            db = self._get_db()
            
            breakdown = await db[dance_breakdowns_collection].find_one({
                "_id": ObjectId(breakdown_id),
                "userId": ObjectId(user_id)
            })
            
            if breakdown is not None:
                breakdown['_id'] = str(breakdown['_id'])
                breakdown['userId'] = str(breakdown['userId'])
                logger.info(f"📋 Retrieved breakdown {breakdown_id} for user {user_id}")
                return breakdown
            else:
                logger.warning(f"❌ Breakdown {breakdown_id} not found for user {user_id}")
                return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get breakdown by ID: {str(e)}")
            raise
    
    async def get_all_breakdown_videos(self, page: int = 1, limit: int = 20) -> Dict:
        """Get all breakdown videos with details for the input screen"""
        try:
            db = self._get_db()
            
            # Debug: Check if collection exists and has data
            total_docs = await db[dance_breakdowns_collection].count_documents({})
            logger.info(f"📊 Total breakdowns in database: {total_docs}")
            
            if total_docs == 0:
                logger.warning("⚠️ No breakdowns found in database")
                return {
                    "breakdowns": [],
                    "total": 0,
                    "page": page,
                    "limit": limit,
                    "hasMore": False
                }
            
            # Calculate skip
            skip = (page - 1) * limit
            
            # Get unique breakdowns by videoUrl (most recent per video)
            pipeline = [
                {
                    "$lookup": {
                        "from": "users",
                        "localField": "userId",
                        "foreignField": "_id",
                        "as": "user"
                    }
                },
                {"$unwind": "$user"},
                # Group by videoUrl to get unique videos (most recent per video)
                {
                    "$group": {
                        "_id": "$videoUrl",
                        "doc": {"$first": "$$ROOT"},
                        "latestCreatedAt": {"$max": "$createdAt"}
                    }
                },
                # Sort by the latest creation date
                {"$sort": {"latestCreatedAt": -1}},
                # Skip and limit for pagination
                {"$skip": skip},
                {"$limit": limit},
                # Project the final structure
                {
                    "$project": {
                        "_id": "$doc._id",
                        "videoUrl": "$doc.videoUrl",
                        "playableVideoUrl": "$doc.playableVideoUrl",
                        "title": "$doc.title",
                        "duration": "$doc.duration",
                        "bpm": "$doc.bpm",
                        "difficultyLevel": "$doc.difficultyLevel",
                        "totalSteps": "$doc.totalSteps",
                        "success": "$doc.success",
                        "createdAt": "$doc.createdAt",
                        "userProfile": {
                            "displayName": "$doc.user.profile.displayName",
                            "avatarUrl": "$doc.user.profile.avatarUrl",
                            "level": "$doc.user.stats.level"
                        }
                    }
                }
            ]
            
            breakdowns = await db[dance_breakdowns_collection].aggregate(pipeline).to_list(length=limit)
            logger.info(f"📊 Retrieved {len(breakdowns)} unique breakdowns from aggregation")
            
            # Get total count of unique videos
            unique_count_pipeline = [
                {"$group": {"_id": "$videoUrl"}},
                {"$count": "total"}
            ]
            unique_count_result = await db[dance_breakdowns_collection].aggregate(unique_count_pipeline).to_list(length=1)
            total = unique_count_result[0]['total'] if unique_count_result else 0
            
            # Convert ObjectIds to strings
            for breakdown in breakdowns:
                breakdown['_id'] = str(breakdown['_id'])
                breakdown['id'] = breakdown['_id']  # Add id field for consistency
                
                # Use actual thumbnail URL from database, or use default
                thumbnail_url = breakdown.get('thumbnailUrl', '')
                if not thumbnail_url:
                    # Use default thumbnail if none exists
                    thumbnail_url = self.get_default_thumbnail_url()
                breakdown['thumbnailUrl'] = thumbnail_url
                
                # Format duration
                if breakdown.get('duration'):
                    minutes = int(breakdown['duration'] // 60)
                    seconds = int(breakdown['duration'] % 60)
                    breakdown['durationFormatted'] = f"{minutes}:{seconds:02d}"
                else:
                    breakdown['durationFormatted'] = "0:00"
            
            logger.info(f"✅ Returning {len(breakdowns)} unique breakdowns")
            return {
                "breakdowns": breakdowns,
                "total": total,
                "page": page,
                "limit": limit,
                "hasMore": (page * limit) < total
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get breakdown videos: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get breakdown videos: {str(e)}")

    
    def extract_audio(self, video_path: str) -> str:
        """Extract audio from video file to WAV format"""
        wav_path = tempfile.mktemp(suffix=".wav")
        
        try:
            # First, let's check if the video file exists and is readable
            if not os.path.exists(video_path):
                raise Exception(f"Video file does not exist: {video_path}")
            
            # Get file size to check if it's not empty
            file_size = os.path.getsize(video_path)
            if file_size == 0:
                raise Exception(f"Video file is empty: {video_path}")
            
            logger.info(f"🎵 Extracting audio from video: {video_path} (size: {file_size} bytes)")
            
            # Run ffmpeg with better error handling
            result = subprocess.run([
            "ffmpeg", "-y",
            "-i", video_path,
            "-vn",  # No video
            "-ac", "1",  # Mono
            "-ar", "44100",  # Sample rate
            wav_path
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"❌ FFmpeg failed with return code {result.returncode}")
                logger.error(f"❌ FFmpeg stderr: {result.stderr}")
                logger.error(f"❌ FFmpeg stdout: {result.stdout}")
                raise Exception(f"FFmpeg failed to extract audio: {result.stderr}")
            
            # Check if the output file was created and has content
            if not os.path.exists(wav_path):
                raise Exception("FFmpeg did not create output WAV file")
            
            wav_size = os.path.getsize(wav_path)
            if wav_size == 0:
                raise Exception("FFmpeg created empty WAV file")
            
            logger.info(f"✅ Audio extraction successful: {wav_path} (size: {wav_size} bytes)")
            return wav_path
            
        except Exception as e:
            logger.error(f"❌ Audio extraction failed: {str(e)}")
            # Clean up the output file if it exists
            if os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except:
                    pass
            raise
    
    def detect_bpm(self, wav_path: str) -> Optional[float]:
        """Detect BPM from audio file using librosa"""
        try:
            y, sr = librosa.load(wav_path, sr=44100, mono=True)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            if tempo == 0:
                return None
            return round(float(tempo), 1)
        except Exception as e:
            logger.error(f"BPM detection failed: {str(e)}")
            return None
    
    def get_video_duration(self, video_path: str) -> float:
        """Get video duration using ffprobe"""
        try:
            cmd = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', video_path]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            duration = float(result.stdout.strip())
            return duration
        except Exception as e:
            logger.warning(f"Failed to get video duration: {str(e)}")
            return 30.0  # Fallback to default duration
    
    def extract_pose_keypoints(self, video_path: str, fps: int = 15) -> List[Dict]:
        """Extract pose keypoints from video frames"""
        cap = cv2.VideoCapture(video_path)
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(round(video_fps / fps))
        results = []
        
        frame_idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % frame_interval == 0:
                timestamp = frame_idx / video_fps
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pose_result = self.mp_pose.process(rgb_frame)
                
                if pose_result.pose_landmarks:
                    keypoints = np.array([[lm.x, lm.y, lm.z, lm.visibility] 
                                        for lm in pose_result.pose_landmarks.landmark])
                else:
                    keypoints = None
                results.append({"timestamp": timestamp, "keypoints": keypoints})
            frame_idx += 1
        
        cap.release()
        return results
    
    def segment_movements(self, pose_keypoints: List[Dict], penalty: int = 5, bpm: Optional[float] = None) -> List[Dict]:
        """Segment movements using change-point detection"""
        valid = [i for i, d in enumerate(pose_keypoints) if d["keypoints"] is not None]
        if len(valid) < 2:
            return []
        
        X = np.stack([pose_keypoints[i]["keypoints"].flatten() for i in valid])
        model = "rbf"
        algo = rpt.Pelt(model=model).fit(X)
        bkps = algo.predict(pen=penalty)
        
        segments = []
        prev = 0
        for bkp in bkps:
            start_idx = valid[prev]
            end_idx = valid[bkp-1] if bkp-1 < len(valid) else valid[-1]
            segments.append({
                "start_idx": start_idx,
                "end_idx": end_idx,
                "start_time": pose_keypoints[start_idx]["timestamp"],
                "end_time": pose_keypoints[end_idx]["timestamp"]
            })
            prev = bkp
        
        # Split long segments at beat intervals if BPM available
        if bpm:
            segments = self._split_segments_by_bpm(segments, bpm, pose_keypoints)
        
        return segments
    
    def _split_segments_by_bpm(self, segments: List[Dict], bpm: float, pose_keypoints: List[Dict]) -> List[Dict]:
        """Split long segments at beat intervals"""
        beat_duration = 60.0 / bpm
        max_step_duration = beat_duration * 4
        new_segments = []
        
        for seg in segments:
            seg_duration = seg["end_time"] - seg["start_time"]
            if seg_duration > max_step_duration:
                t = seg["start_time"]
                while t < seg["end_time"]:
                    next_t = min(t + max_step_duration, seg["end_time"])
                    # Find closest indices
                    start_idx = min(range(len(pose_keypoints)), 
                                  key=lambda j: abs(pose_keypoints[j]["timestamp"] - t))
                    end_idx = min(range(len(pose_keypoints)), 
                                key=lambda j: abs(pose_keypoints[j]["timestamp"] - next_t))
                    new_segments.append({
                        "start_idx": start_idx,
                        "end_idx": end_idx,
                        "start_time": t,
                        "end_time": next_t
                    })
                    t = next_t
            else:
                new_segments.append(seg)
        
        return new_segments
    
    def segment_by_bpm(self, duration: float, bpm: float, beats_per_step: int = 4) -> List[Dict]:
        """Segment video by BPM"""
        beat_duration = 60.0 / bpm
        step_duration = beat_duration * beats_per_step
        segments = []
        t = 0.0
        step_number = 1
        
        while t < duration:
            start_time = t
            end_time = min(t + step_duration, duration)
            segments.append({
                "stepNumber": step_number,
                "start_time": start_time,
                "end_time": end_time,
                "start_idx": None,
                "end_idx": None
            })
            t = end_time
            step_number += 1
        
        return segments
    
    async def analyze_overall_routine(self, segments: List[Dict], pose_keypoints: List[Dict], bpm: float) -> Dict:
        """Analyze the overall routine to establish context"""
        try:
            overall_analysis = {
                "bpm": bpm,
                "total_segments": len(segments),
                "style_indicators": {
                    "rhythm_consistency": "High",
                    "flow_smoothness": "Medium",
                    "symmetry": "Balanced"
                },
                "difficulty_level": "Intermediate",
                "energy_level": "Medium",
                "overall_routine_characteristics": {
                    "tempo": f"The routine is set to a moderate tempo of {bpm} BPM",
                    "rhythm_consistency": "The routine maintains a steady beat",
                    "flow_smoothness": "Transitions between movements are fluid",
                    "symmetry": "The routine has a good balance between left and right movements",
                    "difficulty_level": "Suitable for dancers with some experience",
                    "energy_level": "Engaging and dynamic without being overly exhausting"
                }
            }
            
            # If OpenAI client is not available, return default analysis
            if not self.openai_client:
                logger.warning("OpenAI client not available, using default analysis")
                return overall_analysis
            
            # Make API call with retry mechanism
            max_retries = 3
            retry_delay = 2.0
            
            for attempt in range(max_retries):
                try:
                    response = await self.openai_client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are an expert dance coach analyzing a dance routine. Provide detailed analysis in the exact JSON format specified."},
                            {"role": "user", "content": json.dumps(overall_analysis)}
                        ],
                        temperature=0.7,
                        max_tokens=1000
                    )
                    
                    raw_response = response.choices[0].message.content.strip()
                    logger.info(f"Overall context analysis: {raw_response}")
                    
                    try:
                        context = json.loads(raw_response)
                        required_fields = [
                            "bpm", "total_segments", "style_indicators",
                            "difficulty_level", "energy_level",
                            "overall_routine_characteristics"
                        ]
                        
                        missing_fields = [field for field in required_fields if field not in context]
                        if missing_fields:
                            logger.error(f"Missing required fields in overall context: {missing_fields}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(retry_delay)
                                continue
                            else:
                                return overall_analysis
                        
                        return context
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON parsing error in overall context: {str(e)}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                            continue
                        else:
                            return overall_analysis
                            
                except Exception as e:
                    logger.error(f"Error in API call for overall context: {str(e)}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                        continue
                    else:
                        return overall_analysis
            
            return overall_analysis
            
        except Exception as e:
            logger.error(f"Error in analyze_overall_routine: {str(e)}")
            return overall_analysis
    
    async def generate_step_analysis(self, movement_analysis: Dict, segment: Dict, step_number: int, 
                                   overall_context: Dict) -> Dict:
        """Generate step analysis using OpenAI (only for auto mode)"""
        try:
            # If OpenAI client is not available, return default step
            if not self.openai_client:
                logger.warning("OpenAI client not available, using default step analysis")
                return {
                    "stepNumber": step_number,
                    "startTimestamp": self.format_timestamp(segment.get('start_time', 0)),
                    "endTimestamp": self.format_timestamp(segment.get('end_time', 0)),
                    "stepName": f"Step {step_number}",
                    "global_description": f"Perform step {step_number} with proper form and timing.",
                    "description": {
                        "head": "Keep your head aligned with your spine",
                        "hands": "Maintain natural hand positioning",
                        "shoulders": "Keep shoulders relaxed and level",
                        "torso": "Engage your core for stability",
                        "legs": "Maintain proper stance and balance",
                        "bodyAngle": "Face forward with good posture"
                    },
                    "styleAndHistory": "Modern dance fusion (no OpenAI available)",
                    "spiceItUp": "Add your personal flair to make it unique"
                }
            
            logger.info(f"🤖 Generating OpenAI analysis for step {step_number}")
            
            sys_prompt = """
            You are an expert dance coach and historian.
            Given a summary of body movement (from pose estimation) for a dance segment, generate a very detailed, learnable step.
            Use a casual, friendly, and intuitive tone for all text fields. Avoid repeating words or phrases across steps. Be specific and creative with step names and descriptions, and avoid generic or vague language. Clearly define the key changes in body movement for each step, mentioning which body parts are moving and how.
            Search widely for the dance style, history, and movement details for each step. If the movement is a fusion or not from a classical style, mention that. If you can't find a specific style, say "modern fusion" or "freestyle."
            For each step, also provide a 'global_description': a short, casual, intuitive narration of the whole movement for the step, suitable for a beginner to quickly grasp what to do.
            The 'description' field must be a dictionary with these keys: head, hands, shoulders, torso, legs, bodyAngle — each with a friendly, non-repetitive, and precise description of what to do for that body part in this step.
            Each step object must contain:
              stepNumber (int),
              startTimestamp (MM:SS.sss),
              endTimestamp   (MM:SS.sss),
              stepName,
              global_description (short, casual, intuitive narration),
              description (dictionary as above),
              styleAndHistory (unique for each step),
              spiceItUp (short tip to add personal flavour).
            Respond with ONLY a JSON object for the step.
            """
            
            user_prompt = f"""
            Step number: {step_number}
            Start time: {segment.get('start_time', 0)}
            End time: {segment.get('end_time', 0)}
            Movement summary: {movement_analysis.get('summary', 'No movement data available')}
            Overall context: {json.dumps(overall_context)}
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-2024-05-13",
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            
            raw_content = response.choices[0].message.content
            logger.info(f"Raw OpenAI response for step {step_number}: {raw_content}")
            parsed = json.loads(raw_content)
            
            # Try to extract the step object (if wrapped in a key)
            if isinstance(parsed, dict) and len(parsed) == 1:
                step_obj = list(parsed.values())[0]
            else:
                step_obj = parsed
            
            return step_obj
            
        except Exception as e:
            logger.error(f"Error generating step analysis: {str(e)}")
            return {
                "stepNumber": step_number,
                "startTimestamp": self.format_timestamp(segment.get('start_time', 0)),
                "endTimestamp": self.format_timestamp(segment.get('end_time', 0)),
                "stepName": "Error in analysis",
                "global_description": "Unable to analyze this step",
                "description": {
                    "head": "Error",
                    "hands": "Error",
                    "shoulders": "Error",
                    "torso": "Error",
                    "legs": "Error",
                    "bodyAngle": "Error"
                },
                "styleAndHistory": "Error in analysis",
                "spiceItUp": "Unable to provide tips"
            }
    
    async def analyze_all_movements(self, segments: List[Dict], pose_keypoints: List[Dict], 
                                   bpm: float, mode: str) -> Dict:
        """Analyze all movement segments with individual calls while maintaining context"""
        try:
            logger.info(f"🎬 Analyzing movements in {mode} mode")
            
            if mode == "manual":
                # For manual mode, use default analysis without OpenAI
                overall_context = {
                    "bpm": bpm,
                    "total_segments": len(segments),
                    "style_indicators": {
                        "rhythm_consistency": "Manual Mode",
                        "flow_smoothness": "Manual Mode",
                        "symmetry": "Manual Mode"
                    },
                    "difficulty_level": "Manual Mode",
                    "energy_level": "Manual Mode",
                    "overall_routine_characteristics": {
                        "tempo": f"Manual analysis at {bpm} BPM",
                        "rhythm_consistency": "Manual mode - no AI analysis",
                        "flow_smoothness": "Manual mode - no AI analysis",
                        "symmetry": "Manual mode - no AI analysis",
                        "difficulty_level": "Manual mode - no AI analysis",
                        "energy_level": "Manual mode - no AI analysis"
                    }
                }
            else:
                # For auto mode, use OpenAI analysis
                logger.info("🤖 Using OpenAI for automatic analysis")
                overall_context = await self.analyze_overall_routine(segments, pose_keypoints, bpm)
                if not overall_context:
                    logger.error("Failed to get overall routine context")
                    return {"error": "Failed to analyze routine"}
            
            analyzed_segments = []
            total_segments = len(segments)
            delay_between_requests = 2.0
            
            for i, segment in enumerate(segments):
                try:
                    if mode == "auto" and i > 0:
                        await asyncio.sleep(delay_between_requests)
                    
                    start_time = segment.get("start_time", 0)
                    end_time = segment.get("end_time", 0)
                    
                    if end_time <= start_time:
                        logger.warning(f"Invalid timestamps for segment {i+1}: start={start_time}, end={end_time}")
                        continue
                    
                    start_timestamp = self.format_timestamp(start_time)
                    end_timestamp = self.format_timestamp(end_time)
                    
                    if mode == "manual":
                        # Generate manual step analysis without OpenAI
                        segment_analysis = {
                            "stepNumber": i + 1,
                            "startTimestamp": start_timestamp,
                            "endTimestamp": end_timestamp,
                            "stepName": f"Step {i + 1}",
                            "global_description": f"Perform step {i + 1} with proper form and timing.",
                            "description": {
                                "head": "Keep your head aligned with your spine",
                                "hands": "Maintain natural hand positioning",
                                "shoulders": "Keep shoulders relaxed and level",
                                "torso": "Engage your core for stability",
                                "legs": "Maintain proper stance and balance",
                                "bodyAngle": "Face forward with good posture"
                            },
                            "styleAndHistory": "Modern dance fusion (manual mode)",
                            "spiceItUp": "Add your personal flair to make it unique"
                        }
                        analyzed_segments.append(segment_analysis)
                        continue
                    
                    # For auto mode, analyze movement and use OpenAI
                    movement_analysis = analyze_movement_enhanced(pose_keypoints, segment)
                    
                    # Generate step analysis with OpenAI
                    step_analysis = await self.generate_step_analysis(
                        movement_analysis, segment, i+1, overall_context
                    )
                    
                    analyzed_segments.append(step_analysis)
                    
                except Exception as e:
                    logger.error(f"Error processing segment {i+1}: {str(e)}")
                    continue
            
            if not analyzed_segments:
                logger.error("No segments were successfully analyzed")
                return {"error": "Failed to analyze any segments"}
            
            logger.info(f"✅ Successfully analyzed {len(analyzed_segments)} segments in {mode} mode")
            
            return {
                "mode": mode,
                "overall_analysis": overall_context,
                "segments": analyzed_segments
            }
            
        except Exception as e:
            logger.error(f"Error in analyze_all_movements: {str(e)}")
            return {"error": str(e)}
    
    async def get_breakdown_by_video_url(self, video_url: str) -> Optional[Dict]:
        """Get existing breakdown by video URL (for caching)"""
        try:
            db = self._get_db()
            
            # Look for existing breakdown with the same video URL
            existing_breakdown = await db[dance_breakdowns_collection].find_one({
                "videoUrl": video_url,
                "success": True  # Only return successful breakdowns
            })
            
            if existing_breakdown:
                # Convert ObjectId to string for JSON serialization
                existing_breakdown['_id'] = str(existing_breakdown['_id'])
                existing_breakdown['userId'] = str(existing_breakdown['userId'])
                logger.info(f"🎯 Found existing breakdown for URL: {video_url}")
                return existing_breakdown
            else:
                logger.info(f"🆕 No existing breakdown found for URL: {video_url}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error checking for existing breakdown: {str(e)}")
            return None

    async def convert_db_breakdown_to_response(self, db_breakdown: Dict, mode: str) -> DanceBreakdownResponse:
        """Convert database breakdown to DanceBreakdownResponse"""
        try:
            # Convert steps back to DanceStep objects
            dance_steps = []
            for step_data in db_breakdown.get('steps', []):
                dance_step = DanceStep(
                    step_number=step_data.get('step_number', 0),
                    start_timestamp=step_data.get('start_timestamp', ''),
                    end_timestamp=step_data.get('end_timestamp', ''),
                    step_name=step_data.get('step_name', ''),
                    global_description=step_data.get('global_description', ''),
                    description=step_data.get('description', {}),
                    style_and_history=step_data.get('style_and_history', ''),
                    spice_it_up=step_data.get('spice_it_up', '')
                )
                dance_steps.append(dance_step)
            
            # Create response object
            response = DanceBreakdownResponse(
                success=True,
                video_url=db_breakdown.get('videoUrl', ''),
                playable_video_url=db_breakdown.get('playableVideoUrl', ''),
                title=db_breakdown.get('title', 'Dance Video Analysis'),
                duration=db_breakdown.get('duration', 0.0),
                bpm=db_breakdown.get('bpm'),
                difficulty_level=db_breakdown.get('difficultyLevel', 'Intermediate'),
                total_steps=db_breakdown.get('totalSteps', 0),
                routine_analysis=db_breakdown.get('routineAnalysis', {}),
                steps=dance_steps,
                outline_url=db_breakdown.get('outlineUrl', 'http://localhost:8000/videos/default_outline.mp4'),
                mode=mode
            )
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error converting DB breakdown to response: {str(e)}")
            raise

    async def process_dance_breakdown(self, request: DanceBreakdownRequest, user_id: str) -> DanceBreakdownResponse:
        """Main method to process dance breakdown from URL or S3 file with caching"""
        try:
            logger.info(f"🎬 Starting dance breakdown for user: {user_id}")
            logger.info(f"🎬 Video URL: {request.video_url}")
            logger.info(f"🎬 Mode: {request.mode}")
            
            # Check for existing breakdown (caching)
            existing_breakdown = await self.get_breakdown_by_video_url(request.video_url)
            
            if existing_breakdown:
                logger.info(f"🎯 Using cached breakdown for URL: {request.video_url}")
                
                # Convert database breakdown to response format
                cached_response = await self.convert_db_breakdown_to_response(existing_breakdown, request.mode)
                
                # Update user stats for accessing cached breakdown
                try:
                    db = self._get_db()
                    from services.user.service import update_user_streaks_and_activity_unified
                    await update_user_streaks_and_activity_unified(db, user_id, "breakdown")
                    logger.info(f"✅ Updated user stats for cached breakdown access")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to update user stats for cached breakdown: {str(e)}")
                
                return cached_response
            
            logger.info(f"🆕 Processing new breakdown for URL: {request.video_url}")
            
            # Determine if it's a S3 URL or external URL
            if request.video_url.startswith('https://') and ('s3.amazonaws.com' in request.video_url or 'amazonaws.com' in request.video_url):
                # It's an S3 URL - download from S3
                logger.info(f"🎬 Processing S3 video: {request.video_url}")
                temp_video = await self.download_from_s3(request.video_url)
            else:
                # It's an external URL (YouTube/Instagram) - use existing logic
                logger.info(f"🎬 Processing external URL: {request.video_url}")
                cookies_path = self._get_cookies_path(request.video_url)
                temp_video = await self.download_video(request.video_url, cookies_path)
            
            # Upload video to S3 for client playback
            playable_video_url = await self.upload_video_to_s3(temp_video, user_id, request.video_url)
            
            # Generate and upload thumbnail
            thumbnail_url = await self.generate_and_upload_thumbnail(temp_video, user_id, request.video_url)
            
            # Initialize variables
            wav_path = None
            bpm = None
            
            try:
                # Extract audio and detect BPM (optional - can proceed without it)
                try:
                    wav_path = self.extract_audio(temp_video)
                    bpm = self.detect_bpm(wav_path)
                    logger.info(f"🎵 BPM detected: {bpm}")
                except Exception as audio_error:
                    logger.warning(f"⚠️ Audio extraction/BPM detection failed: {str(audio_error)}")
                    logger.warning(f"⚠️ Proceeding without audio analysis")
                    # Continue without BPM - it's optional
                
                # Extract pose keypoints
                pose_keypoints = self.extract_pose_keypoints(temp_video, fps=15)
                
                # Segment movements
                segments = self.segment_movements(pose_keypoints, penalty=5, bpm=bpm)
                
                # Get actual video duration using ffprobe
                video_duration = self.get_video_duration(temp_video)
                logger.info(f"📹 Video duration: {video_duration:.2f} seconds")
                
                # If not enough segments, use BPM-based segmentation
                min_steps = max(2, int(video_duration // 2))  # at least 1 step per 2 seconds
                if len(segments) < min_steps and bpm:
                    segments = self.segment_by_bpm(video_duration, bpm, beats_per_step=4)
                
                # Analyze all movements
                analysis_result = await self.analyze_all_movements(segments, pose_keypoints, bpm, request.mode)
                
                if "error" in analysis_result:
                    raise Exception(analysis_result["error"])
                
                # Convert segments to DanceStep objects
                dance_steps = []
                for segment in analysis_result["segments"]:
                    dance_step = DanceStep(
                        step_number=segment["stepNumber"],
                        start_timestamp=segment["startTimestamp"],
                        end_timestamp=segment["endTimestamp"],
                        step_name=segment["stepName"],
                        global_description=segment["global_description"],
                        description=segment["description"],
                        style_and_history=segment["styleAndHistory"],
                        spice_it_up=segment["spiceItUp"]
                    )
                    dance_steps.append(dance_step)
                
                # Create response
                response = DanceBreakdownResponse(
                    success=True,
                    video_url=request.video_url,  # Original URL
                    playable_video_url=playable_video_url,  # S3 URL for playback
                    title="Dance Video Analysis",
                    duration=video_duration,  # Actual video duration
                    bpm=bpm,
                    difficulty_level="Intermediate",
                    total_steps=len(dance_steps),
                    routine_analysis=analysis_result["overall_analysis"],
                    steps=dance_steps,
                    outline_url="http://localhost:8000/videos/default_outline.mp4",
                    mode=request.mode
                )
                
                # Save to database
                try:
                    breakdown_id = await self.save_breakdown_to_db(user_id, request, response, thumbnail_url)
                    logger.info(f"💾 Breakdown saved with ID: {breakdown_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to save breakdown to database: {str(e)}")
                    # Continue anyway - don't fail the request if DB save fails
                
                return response
                
            finally:
                # Clean up temporary files
                temp_files = [temp_video]
                if wav_path:
                    temp_files.append(wav_path)
                
                for temp_file in temp_files:
                    if temp_file and os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except Exception as e:
                            logger.warning(f"Failed to clean up temp file {temp_file}: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Error processing dance breakdown: {str(e)}")
            return DanceBreakdownResponse(
                success=False,
                video_url=request.video_url,
                playable_video_url=None,
                title="",
                duration=0.0,
                bpm=None,
                difficulty_level="",
                total_steps=0,
                routine_analysis={},
                steps=[],
                mode=request.mode,
                error_message=str(e)
            )
    
    async def generate_and_upload_thumbnail(self, video_path: str, user_id: str, original_url: str) -> str:
        """Generate thumbnail from video and upload to S3"""
        try:
            import boto3
            from botocore.exceptions import ClientError
            import hashlib
            import os
            import tempfile
            
            # Generate thumbnail using FFmpeg
            thumbnail_path = await self._generate_thumbnail_from_video(video_path)
            
            if not thumbnail_path or not os.path.exists(thumbnail_path):
                logger.warning(f"⚠️ Failed to generate thumbnail for video: {video_path}")
                return ""
            
            # Initialize S3 client
            s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION', 'ap-south-1')
            )
            
            # Generate unique file key for thumbnail
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            url_hash = hashlib.md5(original_url.encode()).hexdigest()[:8]
            thumbnail_key = f"dance-breakdowns/{user_id}/{timestamp}_{url_hash}_thumb.jpg"
            
            # Upload thumbnail to S3
            bucket_name = os.getenv('S3_BUCKET_NAME', 'idanceshreyansh')
            s3_client.upload_file(thumbnail_path, bucket_name, thumbnail_key)
            
            # Generate public URL
            bucket_url = os.getenv('S3_BUCKET_URL', f'https://{bucket_name}.s3.ap-south-1.amazonaws.com')
            thumbnail_url = f"{bucket_url}/{thumbnail_key}"
            
            # Clean up temporary thumbnail file
            try:
                os.remove(thumbnail_path)
            except:
                pass
            
            logger.info(f"✅ Thumbnail uploaded to S3: {thumbnail_url}")
            return thumbnail_url
            
        except Exception as e:
            logger.error(f"❌ Failed to generate/upload thumbnail: {str(e)}")
            return ""
    
    async def _generate_thumbnail_from_video(self, video_path: str) -> Optional[str]:
        """Generate thumbnail from video using FFmpeg"""
        try:
            import tempfile
            import subprocess
            
            # Get video duration to extract frame from middle
            duration = self.get_video_duration(video_path)
            if duration <= 0:
                logger.warning(f"⚠️ Invalid video duration: {duration}")
                return None
            
            # Extract frame from middle of video (at 50% of duration)
            timestamp = duration / 2
            
            # Create temporary file for thumbnail
            thumbnail_path = tempfile.mktemp(suffix=".jpg")
            
            # Use FFmpeg to extract frame
            result = subprocess.run([
                "ffmpeg", "-y",
                "-i", video_path,
                "-ss", str(timestamp),
                "-vframes", "1",
                "-q:v", "2",  # High quality
                "-vf", "scale=480:270",  # 16:9 aspect ratio, reasonable size
                thumbnail_path
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"❌ FFmpeg thumbnail generation failed: {result.stderr}")
                return None
            
            # Check if thumbnail was created
            if not os.path.exists(thumbnail_path):
                logger.error("❌ FFmpeg did not create thumbnail file")
                return None
            
            thumbnail_size = os.path.getsize(thumbnail_path)
            if thumbnail_size == 0:
                logger.error("❌ FFmpeg created empty thumbnail file")
                return None
            
            logger.info(f"✅ Thumbnail generated: {thumbnail_path} (size: {thumbnail_size} bytes)")
            return thumbnail_path
            
        except Exception as e:
            logger.error(f"❌ Thumbnail generation failed: {str(e)}")
            return None

    async def regenerate_missing_thumbnails(self) -> Dict[str, int]:
        """Regenerate thumbnails for breakdowns that don't have them"""
        try:
            db = self._get_db()
            
            # Find breakdowns without thumbnails
            breakdowns_without_thumbnails = await db[dance_breakdowns_collection].find({
                "$or": [
                    {"thumbnailUrl": {"$exists": False}},
                    {"thumbnailUrl": ""},
                    {"thumbnailUrl": None}
                ],
                "playableVideoUrl": {"$exists": True, "$ne": ""}
            }).to_list(length=None)
            
            logger.info(f"🔍 Found {len(breakdowns_without_thumbnails)} breakdowns without thumbnails")
            
            success_count = 0
            failed_count = 0
            
            for breakdown in breakdowns_without_thumbnails:
                try:
                    # Download video from S3
                    video_path = await self.download_from_s3(breakdown['playableVideoUrl'])
                    
                    # Generate thumbnail
                    thumbnail_url = await self.generate_and_upload_thumbnail(
                        video_path, 
                        str(breakdown['userId']), 
                        breakdown['videoUrl']
                    )
                    
                    if thumbnail_url:
                        # Update database with thumbnail URL
                        await db[dance_breakdowns_collection].update_one(
                            {"_id": breakdown['_id']},
                            {"$set": {"thumbnailUrl": thumbnail_url}}
                        )
                        success_count += 1
                        logger.info(f"✅ Regenerated thumbnail for breakdown {breakdown['_id']}")
                    else:
                        failed_count += 1
                        logger.warning(f"⚠️ Failed to generate thumbnail for breakdown {breakdown['_id']}")
                    
                    # Clean up temporary video file
                    try:
                        os.remove(video_path)
                    except:
                        pass
                        
                except Exception as e:
                    failed_count += 1
                    logger.error(f"❌ Error regenerating thumbnail for breakdown {breakdown['_id']}: {str(e)}")
            
            return {
                "total_processed": len(breakdowns_without_thumbnails),
                "success_count": success_count,
                "failed_count": failed_count
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to regenerate missing thumbnails: {str(e)}")
            raise
    
    def get_default_thumbnail_url(self) -> str:
        """Get a default thumbnail URL for fallback"""
        # You can replace this with a static image URL from your S3 bucket
        return "https://via.placeholder.com/480x270/cccccc/666666?text=No+Thumbnail"

    async def get_breakdown_statistics(self) -> Dict:
        """Get statistics about dance breakdowns including cache effectiveness"""
        try:
            db = self._get_db()
            
            # Get total breakdowns
            total_breakdowns = await db[dance_breakdowns_collection].count_documents({})
            
            # Get successful breakdowns
            successful_breakdowns = await db[dance_breakdowns_collection].count_documents({"success": True})
            
            # Get unique video URLs (for cache effectiveness analysis)
            unique_videos_pipeline = [
                {"$group": {"_id": "$videoUrl"}},
                {"$count": "total"}
            ]
            unique_videos_result = await db[dance_breakdowns_collection].aggregate(unique_videos_pipeline).to_list(length=1)
            unique_videos = unique_videos_result[0]['total'] if unique_videos_result else 0
            
            # Get breakdowns by source type
            youtube_breakdowns = await db[dance_breakdowns_collection].count_documents({
                "videoUrl": {"$regex": "youtube\\.com|youtu\\.be"}
            })
            
            instagram_breakdowns = await db[dance_breakdowns_collection].count_documents({
                "videoUrl": {"$regex": "instagram\\.com"}
            })
            
            s3_breakdowns = await db[dance_breakdowns_collection].count_documents({
                "videoUrl": {"$regex": "s3\\.amazonaws\\.com|amazonaws\\.com"}
            })
            
            # Get recent breakdowns (last 7 days)
            from datetime import datetime, timedelta
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_breakdowns = await db[dance_breakdowns_collection].count_documents({
                "createdAt": {"$gte": week_ago}
            })
            
            # Calculate cache efficiency (duplicate URLs indicate cache misses)
            cache_efficiency = 0
            if total_breakdowns > 0:
                cache_efficiency = ((total_breakdowns - unique_videos) / total_breakdowns) * 100
            
            stats = {
                "total_breakdowns": total_breakdowns,
                "successful_breakdowns": successful_breakdowns,
                "unique_videos": unique_videos,
                "cache_efficiency_percentage": round(cache_efficiency, 2),
                "breakdowns_by_source": {
                    "youtube": youtube_breakdowns,
                    "instagram": instagram_breakdowns,
                    "s3": s3_breakdowns,
                    "other": total_breakdowns - youtube_breakdowns - instagram_breakdowns - s3_breakdowns
                },
                "recent_breakdowns_7_days": recent_breakdowns,
                "success_rate_percentage": round((successful_breakdowns / total_breakdowns * 100) if total_breakdowns > 0 else 0, 2)
            }
            
            logger.info(f"📊 Breakdown statistics: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting breakdown statistics: {str(e)}")
            return {
                "error": str(e),
                "total_breakdowns": 0,
                "successful_breakdowns": 0,
                "unique_videos": 0,
                "cache_efficiency_percentage": 0
            }

    async def clear_duplicate_breakdowns(self) -> Dict:
        """Remove duplicate breakdowns for the same video URL, keeping only the most recent successful one"""
        try:
            db = self._get_db()
            
            # Find duplicate URLs
            duplicate_pipeline = [
                {"$group": {
                    "_id": "$videoUrl",
                    "count": {"$sum": 1},
                    "breakdowns": {"$push": {
                        "_id": "$_id",
                        "createdAt": "$createdAt",
                        "success": "$success"
                    }}
                }},
                {"$match": {"count": {"$gt": 1}}},
                {"$sort": {"_id": 1}}
            ]
            
            duplicates = await db[dance_breakdowns_collection].aggregate(duplicate_pipeline).to_list(length=None)
            
            total_removed = 0
            
            for duplicate in duplicates:
                video_url = duplicate["_id"]
                breakdowns = duplicate["breakdowns"]
                
                # Sort by creation date (newest first) and success status
                breakdowns.sort(key=lambda x: (x["success"], x["createdAt"]), reverse=True)
                
                # Keep the first one (most recent successful, or most recent if none successful)
                to_keep = breakdowns[0]
                to_remove = breakdowns[1:]
                
                # Remove duplicates
                for breakdown in to_remove:
                    await db[dance_breakdowns_collection].delete_one({"_id": breakdown["_id"]})
                    total_removed += 1
                
                logger.info(f"🧹 Cleaned up {len(to_remove)} duplicates for URL: {video_url}")
            
            logger.info(f"✅ Removed {total_removed} duplicate breakdowns")
            return {
                "total_removed": total_removed,
                "duplicate_urls_processed": len(duplicates)
            }
            
        except Exception as e:
            logger.error(f"❌ Error clearing duplicate breakdowns: {str(e)}")
            return {"error": str(e), "total_removed": 0}

# Create service instance
dance_breakdown_service = DanceBreakdownService() 