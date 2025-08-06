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
from datetime import datetime
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
        
        # Clean URL to extract just the video ID (remove playlist parameters)
        clean_url = self._clean_youtube_url(url)
        logger.info(f"Attempting to download: {clean_url}")
        
        # Multiple download strategies to try
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
        error_msg = f"All download strategies failed for {url}. This video may be:"
        error_msg += "\n- Geo-restricted or region-locked"
        error_msg += "\n- Age-restricted requiring sign-in"
        error_msg += "\n- Private or deleted"
        error_msg += "\n- Protected by YouTube's anti-bot measures"
        error_msg += "\nTry using a different video URL."
        
        logger.error(error_msg)
        raise Exception(error_msg)
    
    async def upload_video_to_s3(self, video_path: str, user_id: str, original_url: str) -> str:
        """Upload downloaded video to S3 and return playable URL"""
        try:
            import boto3
            from botocore.exceptions import ClientError
            import hashlib
            import os
            
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
            
            # Upload to S3
            bucket_name = os.getenv('S3_BUCKET_NAME', 'idanceshreyansh')
            s3_client.upload_file(video_path, bucket_name, file_key)
            
            # Generate public URL
            bucket_url = os.getenv('S3_BUCKET_URL', f'https://{bucket_name}.s3.ap-south-1.amazonaws.com')
            video_url = f"{bucket_url}/{file_key}"
            
            logger.info(f"✅ Video uploaded to S3: {video_url}")
            return video_url
            
        except Exception as e:
            logger.error(f"❌ Failed to upload video to S3: {str(e)}")
            # Return original URL as fallback
            return original_url
    
    def _get_db(self):
        """Get database connection"""
        if self.db is None:
            self.db = Database.get_database()
        return self.db
    
    async def save_breakdown_to_db(self, user_id: str, request: DanceBreakdownRequest, response: DanceBreakdownResponse) -> str:
        """Save dance breakdown to database"""
        try:
            db = self._get_db()
            
            breakdown_doc = {
                "userId": ObjectId(user_id),
                "videoUrl": request.video_url,
                "playableVideoUrl": response.playable_video_url,
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
            
            result = await db['dance_breakdowns'].insert_one(breakdown_doc)
            breakdown_id = str(result.inserted_id)
            
            logger.info(f"✅ Breakdown saved to database with ID: {breakdown_id}")
            return breakdown_id
            
        except Exception as e:
            logger.error(f"❌ Failed to save breakdown to database: {str(e)}")
            raise
    
    async def get_user_breakdowns(self, user_id: str, limit: int = 20, skip: int = 0) -> List[Dict]:
        """Get user's dance breakdown history"""
        try:
            db = self._get_db()
            
            cursor = db['dance_breakdowns'].find(
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
            
            breakdown = await db['dance_breakdowns'].find_one({
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
            total_docs = await db['dance_breakdowns'].count_documents({})
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
            
            # Get breakdowns with user info
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
                {
                    "$project": {
                        "_id": 1,
                        "videoUrl": 1,
                        "playableVideoUrl": 1,
                        "title": 1,
                        "duration": 1,
                        "bpm": 1,
                        "difficultyLevel": 1,
                        "totalSteps": 1,
                        "success": 1,
                        "createdAt": 1,
                        "userProfile": {
                            "displayName": "$user.profile.displayName",
                            "avatarUrl": "$user.profile.avatarUrl",
                            "level": "$user.stats.level"
                        }
                    }
                },
                {"$sort": {"createdAt": -1}},
                {"$skip": skip},
                {"$limit": limit}
            ]
            
            breakdowns = await db['dance_breakdowns'].aggregate(pipeline).to_list(length=limit)
            logger.info(f"📊 Retrieved {len(breakdowns)} breakdowns from aggregation")
            
            # Get total count
            total = await db['dance_breakdowns'].count_documents({})
            
            # Convert ObjectIds to strings
            for breakdown in breakdowns:
                breakdown['_id'] = str(breakdown['_id'])
                breakdown['id'] = breakdown['_id']  # Add id field for consistency
                
                # Generate thumbnail URL (you can implement thumbnail generation later)
                breakdown['thumbnailUrl'] = breakdown.get('playableVideoUrl', '').replace('.mp4', '_thumb.jpg')
                
                # Format duration
                if breakdown.get('duration'):
                    minutes = int(breakdown['duration'] // 60)
                    seconds = int(breakdown['duration'] % 60)
                    breakdown['durationFormatted'] = f"{minutes}:{seconds:02d}"
                else:
                    breakdown['durationFormatted'] = "0:00"
            
            logger.info(f"✅ Returning {len(breakdowns)} breakdowns")
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
        subprocess.run([
            "ffmpeg", "-y",
            "-i", video_path,
            "-vn",  # No video
            "-ac", "1",  # Mono
            "-ar", "44100",  # Sample rate
            wav_path
        ], check=True, capture_output=True)
        return wav_path
    
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
    
    async def process_dance_breakdown(self, request: DanceBreakdownRequest, user_id: str) -> DanceBreakdownResponse:
        """Main method to process dance breakdown from URL"""
        try:
            logger.info(f"🎬 Starting dance breakdown for URL: {request.video_url}")
            logger.info(f"🎬 Mode: {request.mode}")
            
            # Determine cookies file based on URL
            cookies_path = None
            if "instagram.com" in request.video_url:
                cookies_path = 'cookies_instagram.txt'
            else:
                cookies_path = 'cookies_youtube.txt'
            
            # Check if cookies file exists and is valid
            if cookies_path and os.path.exists(cookies_path):
                try:
                    # Test if cookies file is valid by reading first few lines
                    with open(cookies_path, 'r') as f:
                        first_line = f.readline().strip()
                        if first_line.startswith('#') or first_line.startswith('.'):
                            logger.info(f"Using cookies file: {cookies_path}")
                        else:
                            logger.warning(f"Invalid cookies file format: {cookies_path}")
                            cookies_path = None
                except Exception as e:
                    logger.warning(f"Error reading cookies file: {str(e)}")
                    cookies_path = None
            else:
                logger.info("No cookies file found, proceeding without authentication")
                cookies_path = None
            
            # Download video
            temp_video = await self.download_video(request.video_url, cookies_path)
            
            # Upload video to S3 for client playback
            playable_video_url = await self.upload_video_to_s3(temp_video, user_id, request.video_url)
            
            try:
                # Extract audio and detect BPM
                wav_path = self.extract_audio(temp_video)
                bpm = self.detect_bpm(wav_path)
                
                # Extract pose keypoints
                pose_keypoints = self.extract_pose_keypoints(temp_video, fps=15)
                
                # Segment movements
                segments = self.segment_movements(pose_keypoints, penalty=5, bpm=bpm)
                
                # If not enough segments, use BPM-based segmentation
                min_steps = max(2, int(30 // 2))  # at least 1 step per 2 seconds
                if len(segments) < min_steps and bpm:
                    segments = self.segment_by_bpm(30, bpm, beats_per_step=4)
                
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
                    duration=30.0,  # Default duration
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
                    breakdown_id = await self.save_breakdown_to_db(user_id, request, response)
                    logger.info(f"💾 Breakdown saved with ID: {breakdown_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to save breakdown to database: {str(e)}")
                    # Continue anyway - don't fail the request if DB save fails
                
                return response
                
            finally:
                # Clean up temporary files
                for temp_file in [temp_video, wav_path]:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        
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

# Create service instance
dance_breakdown_service = DanceBreakdownService() 