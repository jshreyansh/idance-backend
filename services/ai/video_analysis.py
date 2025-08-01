#!/usr/bin/env python3
"""
Real Video Analysis Service using MediaPipe
"""

import cv2
import mediapipe as mp
import numpy as np
import json
import tempfile
import os
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from services.ai.models import PoseKeypoint, PoseFrame, PoseAnalysisResult

logger = logging.getLogger(__name__)

class VideoAnalysisService:
    """Service for analyzing dance videos using MediaPipe pose detection"""
    
    def __init__(self):
        # Initialize MediaPipe pose detection
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Configure pose detection
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,  # 0, 1, or 2 (higher = more accurate but slower)
            smooth_landmarks=True,
            enable_segmentation=False,
            smooth_segmentation=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Pose landmark mapping
        self.landmark_names = {
            0: "nose",
            1: "left_eye_inner", 2: "left_eye", 3: "left_eye_outer",
            4: "right_eye_inner", 5: "right_eye", 6: "right_eye_outer",
            7: "left_ear", 8: "right_ear",
            9: "mouth_left", 10: "mouth_right",
            11: "left_shoulder", 12: "right_shoulder",
            13: "left_elbow", 14: "right_elbow",
            15: "left_wrist", 16: "right_wrist",
            17: "left_pinky", 18: "right_pinky",
            19: "left_index", 20: "right_index",
            21: "left_thumb", 22: "right_thumb",
            23: "left_hip", 24: "right_hip",
            25: "left_knee", 26: "right_knee",
            27: "left_ankle", 28: "right_ankle",
            29: "left_heel", 30: "right_heel",
            31: "left_foot_index", 32: "right_foot_index"
        }
    
    async def analyze_video(self, video_url: str, submission_id: str) -> PoseAnalysisResult:
        """
        Analyze a dance video and extract pose data
        """
        try:
            logger.info(f"🎬 Starting video analysis for submission {submission_id}")
            logger.info(f"📹 Video URL: {video_url}")
            start_time = datetime.utcnow()
            
            # Download video to temporary file
            logger.info(f"📥 Downloading video from {video_url}")
            video_path = await self._download_video(video_url)
            
            if not video_path:
                logger.error(f"❌ Failed to download video from {video_url}")
                raise Exception("Failed to download video")
            else:
                logger.info(f"✅ Video downloaded successfully to {video_path}")
            
            # Analyze video frames
            logger.info(f"🎬 Extracting pose frames from video")
            pose_frames = await self._extract_pose_frames(video_path)
            logger.info(f"✅ Extracted {len(pose_frames)} pose frames")
            
            # Clean up temporary file
            os.remove(video_path)
            
            # Calculate analysis confidence
            total_frames = len(pose_frames)
            frames_with_pose = sum(1 for frame in pose_frames if frame.frame_confidence > 0.5)
            analysis_confidence = frames_with_pose / total_frames if total_frames > 0 else 0
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(f"✅ Video analysis completed for submission {submission_id}")
            logger.info(f"📊 Processed {total_frames} frames, {frames_with_pose} with pose detection")
            
            return PoseAnalysisResult(
                submission_id=submission_id,
                total_frames=total_frames,
                frames_analyzed=frames_with_pose,
                pose_frames=pose_frames,
                analysis_confidence=analysis_confidence,
                processing_time=processing_time,
                created_at=start_time
            )
            
        except Exception as e:
            logger.error(f"❌ Error in video analysis: {e}")
            raise
    
    async def _download_video(self, video_url: str) -> Optional[str]:
        """Download video to temporary file"""
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            temp_path = temp_file.name
            temp_file.close()
            
            # Download video
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"📥 Downloaded video to {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"❌ Error downloading video: {e}")
            return None
    
    async def _extract_pose_frames(self, video_path: str) -> List[PoseFrame]:
        """Extract pose data from video frames"""
        pose_frames = []
        
        try:
            # Open video file
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise Exception("Could not open video file")
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            logger.info(f"📹 Video: {frame_count} frames at {fps} FPS")
            
            frame_number = 0
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process frame for pose detection
                pose_frame = await self._process_frame(frame, frame_number, fps)
                if pose_frame:
                    pose_frames.append(pose_frame)
                
                frame_number += 1
                
                # Log progress every 30 frames
                if frame_number % 30 == 0:
                    logger.info(f"🔄 Processed {frame_number}/{frame_count} frames")
            
            cap.release()
            
            logger.info(f"✅ Extracted pose data from {len(pose_frames)} frames")
            return pose_frames
            
        except Exception as e:
            logger.error(f"❌ Error extracting pose frames: {e}")
            return []
    
    async def _process_frame(self, frame: np.ndarray, frame_number: int, fps: float) -> Optional[PoseFrame]:
        """Process a single frame for pose detection"""
        try:
            # Convert BGR to RGB (MediaPipe expects RGB)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process with MediaPipe
            results = self.pose.process(rgb_frame)
            
            if not results.pose_landmarks:
                # No pose detected in this frame
                return PoseFrame(
                    frame_number=frame_number,
                    timestamp=frame_number / fps,
                    keypoints=[],
                    frame_confidence=0.0
                )
            
            # Extract pose landmarks
            keypoints = []
            total_confidence = 0.0
            valid_landmarks = 0
            
            for landmark_id, landmark in enumerate(results.pose_landmarks.landmark):
                if landmark.visibility > 0.5:  # Only include visible landmarks
                    keypoint = PoseKeypoint(
                        x=landmark.x,
                        y=landmark.y,
                        confidence=landmark.visibility,
                        keypoint_type=self.landmark_names.get(landmark_id, f"landmark_{landmark_id}")
                    )
                    keypoints.append(keypoint)
                    total_confidence += landmark.visibility
                    valid_landmarks += 1
            
            # Calculate frame confidence
            frame_confidence = total_confidence / valid_landmarks if valid_landmarks > 0 else 0.0
            
            return PoseFrame(
                frame_number=frame_number,
                timestamp=frame_number / fps,
                keypoints=keypoints,
                frame_confidence=frame_confidence
            )
            
        except Exception as e:
            logger.error(f"❌ Error processing frame {frame_number}: {e}")
            return None
    
    def calculate_balance_score(self, pose_frames: List[PoseFrame]) -> int:
        """Calculate balance score based on pose stability"""
        if not pose_frames:
            return 0
        
        try:
            # Analyze center of mass stability
            com_positions = []
            
            for frame in pose_frames:
                if len(frame.keypoints) >= 17:  # Need hip and shoulder points
                    # Calculate center of mass (average of hip and shoulder positions)
                    hip_points = [kp for kp in frame.keypoints if "hip" in kp.keypoint_type or "shoulder" in kp.keypoint_type]
                    
                    if hip_points:
                        avg_x = sum(kp.x for kp in hip_points) / len(hip_points)
                        avg_y = sum(kp.y for kp in hip_points) / len(hip_points)
                        com_positions.append((avg_x, avg_y))
            
            if len(com_positions) < 10:
                return 10  # Not enough data
            
            # Calculate stability (lower variance = better balance)
            x_positions = [pos[0] for pos in com_positions]
            y_positions = [pos[1] for pos in com_positions]
            
            x_variance = np.var(x_positions)
            y_variance = np.var(y_positions)
            
            # Score based on stability (0-25 points)
            stability_score = max(0, 25 - int((x_variance + y_variance) * 100))
            
            return min(25, stability_score)
            
        except Exception as e:
            logger.error(f"❌ Error calculating balance score: {e}")
            return 15  # Default score
    
    def calculate_rhythm_score(self, pose_frames: List[PoseFrame], target_bpm: Optional[int] = None) -> int:
        """Calculate rhythm score based on movement patterns"""
        if not pose_frames:
            return 0
        
        try:
            # Analyze movement frequency and consistency
            movement_scores = []
            
            for i in range(1, len(pose_frames)):
                prev_frame = pose_frames[i-1]
                curr_frame = pose_frames[i]
                
                if prev_frame.keypoints and curr_frame.keypoints:
                    # Calculate movement between frames
                    movement = self._calculate_frame_movement(prev_frame, curr_frame)
                    movement_scores.append(movement)
            
            if not movement_scores:
                return 15  # Default score
            
            # Analyze rhythm consistency
            avg_movement = np.mean(movement_scores)
            movement_variance = np.var(movement_scores)
            
            # Score based on consistent movement patterns (0-30 points)
            rhythm_score = max(0, 30 - int(movement_variance * 50))
            
            return min(30, rhythm_score)
            
        except Exception as e:
            logger.error(f"❌ Error calculating rhythm score: {e}")
            return 20  # Default score
    
    def calculate_smoothness_score(self, pose_frames: List[PoseFrame]) -> int:
        """Calculate movement smoothness score"""
        if not pose_frames:
            return 0
        
        try:
            # Analyze smoothness of joint movements
            smoothness_scores = []
            
            for i in range(2, len(pose_frames)):
                prev_frame = pose_frames[i-2]
                curr_frame = pose_frames[i-1]
                next_frame = pose_frames[i]
                
                if all([prev_frame.keypoints, curr_frame.keypoints, next_frame.keypoints]):
                    # Calculate smoothness (how linear the movement is)
                    smoothness = self._calculate_movement_smoothness(prev_frame, curr_frame, next_frame)
                    smoothness_scores.append(smoothness)
            
            if not smoothness_scores:
                return 15  # Default score
            
            # Score based on movement smoothness (0-25 points)
            avg_smoothness = np.mean(smoothness_scores)
            smoothness_score = int(avg_smoothness * 25)
            
            return min(25, smoothness_score)
            
        except Exception as e:
            logger.error(f"❌ Error calculating smoothness score: {e}")
            return 18  # Default score
    
    def calculate_creativity_score(self, pose_frames: List[PoseFrame]) -> int:
        """Calculate creativity score based on movement variety"""
        if not pose_frames:
            return 0
        
        try:
            # Analyze movement variety and complexity
            movement_variety = self._calculate_movement_variety(pose_frames)
            
            # Score based on movement variety (0-20 points)
            creativity_score = int(movement_variety * 20)
            
            return min(20, creativity_score)
            
        except Exception as e:
            logger.error(f"❌ Error calculating creativity score: {e}")
            return 12  # Default score
    
    def _calculate_frame_movement(self, frame1: PoseFrame, frame2: PoseFrame) -> float:
        """Calculate movement between two frames"""
        if not frame1.keypoints or not frame2.keypoints:
            return 0.0
        
        total_movement = 0.0
        valid_pairs = 0
        
        # Create mapping of keypoints by type
        frame1_map = {kp.keypoint_type: kp for kp in frame1.keypoints}
        frame2_map = {kp.keypoint_type: kp for kp in frame2.keypoints}
        
        for kp_type in frame1_map:
            if kp_type in frame2_map:
                kp1 = frame1_map[kp_type]
                kp2 = frame2_map[kp_type]
                
                # Calculate Euclidean distance
                distance = np.sqrt((kp2.x - kp1.x)**2 + (kp2.y - kp1.y)**2)
                total_movement += distance
                valid_pairs += 1
        
        return total_movement / valid_pairs if valid_pairs > 0 else 0.0
    
    def _calculate_movement_smoothness(self, frame1: PoseFrame, frame2: PoseFrame, frame3: PoseFrame) -> float:
        """Calculate smoothness of movement across three frames"""
        if not all([frame1.keypoints, frame2.keypoints, frame3.keypoints]):
            return 0.0
        
        # Calculate linearity of movement
        # Higher smoothness = more linear movement
        movement1 = self._calculate_frame_movement(frame1, frame2)
        movement2 = self._calculate_frame_movement(frame2, frame3)
        
        # Smoothness is inversely proportional to acceleration
        acceleration = abs(movement2 - movement1)
        smoothness = max(0, 1.0 - acceleration)
        
        return smoothness
    
    def _calculate_movement_variety(self, pose_frames: List[PoseFrame]) -> float:
        """Calculate variety of movements"""
        if len(pose_frames) < 10:
            return 0.5  # Default variety
        
        # Analyze different types of movements
        movement_types = set()
        
        for i in range(1, len(pose_frames)):
            frame1 = pose_frames[i-1]
            frame2 = pose_frames[i]
            
            if frame1.keypoints and frame2.keypoints:
                # Categorize movement type
                movement_type = self._categorize_movement(frame1, frame2)
                movement_types.add(movement_type)
        
        # Variety score based on number of different movement types
        variety_score = min(1.0, len(movement_types) / 10.0)
        
        return variety_score
    
    def _categorize_movement(self, frame1: PoseFrame, frame2: PoseFrame) -> str:
        """Categorize the type of movement between frames"""
        if not frame1.keypoints or not frame2.keypoints:
            return "static"
        
        # Analyze which body parts moved the most
        arm_movement = 0
        leg_movement = 0
        torso_movement = 0
        
        frame1_map = {kp.keypoint_type: kp for kp in frame1.keypoints}
        frame2_map = {kp.keypoint_type: kp for kp in frame2.keypoints}
        
        # Arm movement
        arm_points = ["left_shoulder", "right_shoulder", "left_elbow", "right_elbow", "left_wrist", "right_wrist"]
        for point in arm_points:
            if point in frame1_map and point in frame2_map:
                distance = np.sqrt((frame2_map[point].x - frame1_map[point].x)**2 + 
                                 (frame2_map[point].y - frame1_map[point].y)**2)
                arm_movement += distance
        
        # Leg movement
        leg_points = ["left_hip", "right_hip", "left_knee", "right_knee", "left_ankle", "right_ankle"]
        for point in leg_points:
            if point in frame1_map and point in frame2_map:
                distance = np.sqrt((frame2_map[point].x - frame1_map[point].x)**2 + 
                                 (frame2_map[point].y - frame1_map[point].y)**2)
                leg_movement += distance
        
        # Torso movement
        torso_points = ["left_shoulder", "right_shoulder", "left_hip", "right_hip"]
        for point in torso_points:
            if point in frame1_map and point in frame2_map:
                distance = np.sqrt((frame2_map[point].x - frame1_map[point].x)**2 + 
                                 (frame2_map[point].y - frame1_map[point].y)**2)
                torso_movement += distance
        
        # Categorize based on dominant movement
        max_movement = max(arm_movement, leg_movement, torso_movement)
        
        if max_movement < 0.01:
            return "static"
        elif arm_movement == max_movement:
            return "arm_movement"
        elif leg_movement == max_movement:
            return "leg_movement"
        else:
            return "torso_movement"

# Global service instance
video_analysis_service = VideoAnalysisService() 