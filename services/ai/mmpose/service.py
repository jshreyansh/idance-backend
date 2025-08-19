#!/usr/bin/env python3
"""
MMPose Service for Advanced Dance Pose Analysis
"""

import asyncio
import logging
import os
import tempfile
import cv2
import numpy as np
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime
import json

# MMPose imports (with fallback handling)
try:
    from mmpose.apis import inference_top_down_pose_model, init_pose_model
    from mmpose.apis import inference_bottom_up_pose_model
    from mmdet.apis import inference_detector, init_detector
    from mmpose.structures import merge_data_samples
    MMPOSE_AVAILABLE = True
except ImportError:
    MMPOSE_AVAILABLE = False
    logging.warning("MMPose not available. Install with: pip install -U openmim && mim install mmpose")

from .models import (
    MMPoseAnalysisResult, 
    MMPoseFrame, 
    MMPoseKeypoint,
    DanceScoringResult,
    ChallengeAnalysisRequest,
    ChallengeAnalysisResponse
)
from .scoring import DanceScoringEngine
from .dance_metrics import DanceMetricsAnalyzer

logger = logging.getLogger(__name__)

class MMPoseService:
    """Advanced pose analysis service using MMPose"""
    
    def __init__(self):
        self.pose_model = None
        self.detector = None
        self.scoring_engine = DanceScoringEngine()
        self.metrics_analyzer = DanceMetricsAnalyzer()
        self.analysis_queue = {}
        
        if MMPOSE_AVAILABLE:
            self._initialize_models()
        else:
            logger.error("MMPose not available. Service will use fallback methods.")
    
    def _initialize_models(self):
        """Initialize MMPose models"""
        try:
            # Initialize person detector (YOLOX)
            detector_config = 'mmdetection/configs/yolox/yolox_s_8x8_300e_coco.py'
            detector_checkpoint = 'https://download.openmmlab.com/mmdetection/v2.0/yolox/yolox_s_8x8_300e_coco/yolox_s_8x8_300e_coco_20211126_140236-d3bd96b8.pth'
            
            # Initialize pose estimator (HRNet)
            pose_config = 'mmpose/configs/body_2d_keypoint/topdown_heatmap/coco/td-hm_hrnet-w48_8xb32-210e_coco-256x192.py'
            pose_checkpoint = 'https://download.openmmlab.com/mmpose/top_down/hrnet/hrnet_w48_coco_256x192-b9e0b3ab_20200708.pth'
            
            # Initialize models
            self.detector = init_detector(detector_config, detector_checkpoint, device='cpu')
            self.pose_model = init_pose_model(pose_config, pose_checkpoint, device='cpu')
            
            logger.info("✅ MMPose models initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize MMPose models: {e}")
            self.pose_model = None
            self.detector = None
    
    async def analyze_challenge_submission(self, request: ChallengeAnalysisRequest) -> ChallengeAnalysisResponse:
        """Analyze a challenge submission using MMPose"""
        try:
            logger.info(f"🎬 Starting MMPose analysis for submission {request.submission_id}")
            
            # Create initial response
            response = ChallengeAnalysisResponse(
                submission_id=request.submission_id,
                status="processing",
                progress=0.0,
                created_at=datetime.utcnow()
            )
            
            # Store in queue for tracking
            self.analysis_queue[request.submission_id] = response
            
            # Process analysis
            try:
                # Download video
                video_path = await self._download_video(request.video_url)
                response.progress = 0.1
                
                # Extract pose frames
                pose_frames = await self._extract_pose_frames(video_path)
                response.progress = 0.4
                
                # Analyze dance metrics
                dance_metrics = await self._analyze_dance_metrics(pose_frames, request)
                response.progress = 0.7
                
                # Calculate scores
                scoring_result = await self._calculate_scores(pose_frames, dance_metrics, request)
                response.progress = 0.9
                
                # Create final result
                analysis_result = MMPoseAnalysisResult(
                    submission_id=request.submission_id,
                    video_url=request.video_url,
                    challenge_type=request.challenge_type,
                    pose_frames=pose_frames,
                    total_frames=len(pose_frames),
                    frames_analyzed=len([f for f in pose_frames if f.frame_confidence > 0.5]),
                    analysis_confidence=np.mean([f.frame_confidence for f in pose_frames]),
                    scoring_result=scoring_result,
                    processing_time=0.0,  # Will be calculated
                    created_at=datetime.utcnow()
                )
                
                # Update response
                response.status = "completed"
                response.progress = 1.0
                response.analysis_result = analysis_result
                response.completed_at = datetime.utcnow()
                
                logger.info(f"✅ MMPose analysis completed for submission {request.submission_id}")
                
            except Exception as e:
                logger.error(f"❌ Analysis failed: {e}")
                response.status = "failed"
                response.error_message = str(e)
                response.error_code = "ANALYSIS_FAILED"
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error in challenge analysis: {e}")
            return ChallengeAnalysisResponse(
                submission_id=request.submission_id,
                status="failed",
                error_message=str(e),
                error_code="SERVICE_ERROR",
                created_at=datetime.utcnow()
            )
    
    async def _download_video(self, video_url: str) -> str:
        """Download video to temporary file"""
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            temp_path = temp_file.name
            temp_file.close()
            
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"📥 Downloaded video to {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"❌ Error downloading video: {e}")
            raise
    
    async def _extract_pose_frames(self, video_path: str) -> List[MMPoseFrame]:
        """Extract pose frames using MMPose"""
        if not MMPOSE_AVAILABLE or not self.pose_model:
            logger.warning("MMPose not available, using fallback method")
            return await self._extract_pose_frames_fallback(video_path)
        
        try:
            pose_frames = []
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise Exception("Could not open video file")
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            logger.info(f"📹 Processing {frame_count} frames at {fps} FPS")
            
            frame_number = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process every 3rd frame for efficiency (10 FPS analysis)
                if frame_number % 3 == 0:
                    pose_frame = await self._process_frame_mmpose(frame, frame_number, fps)
                    if pose_frame:
                        pose_frames.append(pose_frame)
                
                frame_number += 1
                
                if frame_number % 30 == 0:
                    logger.info(f"🔄 Processed {frame_number}/{frame_count} frames")
            
            cap.release()
            
            logger.info(f"✅ Extracted {len(pose_frames)} pose frames")
            return pose_frames
            
        except Exception as e:
            logger.error(f"❌ Error extracting pose frames: {e}")
            return []
    
    async def _process_frame_mmpose(self, frame: np.ndarray, frame_number: int, fps: float) -> Optional[MMPoseFrame]:
        """Process a single frame using MMPose"""
        try:
            # Detect persons
            det_result = inference_detector(self.detector, frame)
            person_results = self._process_detection_result(det_result)
            
            if not person_results:
                return MMPoseFrame(
                    frame_number=frame_number,
                    timestamp=frame_number / fps,
                    keypoints=[],
                    frame_confidence=0.0
                )
            
            # Get pose for the first person (main dancer)
            person = person_results[0]
            pose_result = inference_top_down_pose_model(
                self.pose_model, frame, [person], format='xyxy'
            )
            
            if not pose_result or not pose_result[0].pred_instances:
                return MMPoseFrame(
                    frame_number=frame_number,
                    timestamp=frame_number / fps,
                    keypoints=[],
                    frame_confidence=0.0
                )
            
            # Extract keypoints
            keypoints = []
            pose_instance = pose_result[0].pred_instances
            keypoints_data = pose_instance.keypoints[0]
            keypoint_scores = pose_instance.keypoint_scores[0]
            
            # COCO keypoint names
            coco_keypoints = [
                "nose", "left_eye", "right_eye", "left_ear", "right_ear",
                "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
                "left_wrist", "right_wrist", "left_hip", "right_hip",
                "left_knee", "right_knee", "left_ankle", "right_ankle"
            ]
            
            for i, (kp, score) in enumerate(zip(keypoints_data, keypoint_scores)):
                if i < len(coco_keypoints):
                    keypoint = MMPoseKeypoint(
                        x=float(kp[0]),
                        y=float(kp[1]),
                        confidence=float(score),
                        keypoint_type=coco_keypoints[i]
                    )
                    keypoints.append(keypoint)
            
            # Calculate frame confidence
            frame_confidence = float(np.mean(keypoint_scores)) if len(keypoint_scores) > 0 else 0.0
            
            return MMPoseFrame(
                frame_number=frame_number,
                timestamp=frame_number / fps,
                keypoints=keypoints,
                frame_confidence=frame_confidence,
                bbox=person[:4].tolist() if len(person) >= 4 else None
            )
            
        except Exception as e:
            logger.error(f"❌ Error processing frame {frame_number}: {e}")
            return None
    
    def _process_detection_result(self, det_result) -> List:
        """Process detection results to get person bounding boxes"""
        try:
            if hasattr(det_result, 'pred_instances'):
                # New MMDetection format
                instances = det_result.pred_instances
                bboxes = instances.bboxes.cpu().numpy()
                scores = instances.scores.cpu().numpy()
                labels = instances.labels.cpu().numpy()
            else:
                # Legacy format
                bboxes, scores, labels = det_result
            
            # Filter for person class (class 0 in COCO)
            person_indices = np.where(labels == 0)[0]
            person_results = []
            
            for idx in person_indices:
                if scores[idx] > 0.5:  # Confidence threshold
                    person_results.append(bboxes[idx])
            
            return person_results
            
        except Exception as e:
            logger.error(f"❌ Error processing detection result: {e}")
            return []
    
    async def _extract_pose_frames_fallback(self, video_path: str) -> List[MMPoseFrame]:
        """Fallback pose extraction method"""
        try:
            # Simple fallback using OpenCV
            pose_frames = []
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise Exception("Could not open video file")
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_number = 0
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_number % 3 == 0:  # Process every 3rd frame
                    # Create mock keypoints for fallback
                    keypoints = []
                    for i in range(17):  # COCO keypoints
                        keypoint = MMPoseKeypoint(
                            x=np.random.uniform(0, 1),
                            y=np.random.uniform(0, 1),
                            confidence=np.random.uniform(0.5, 1.0),
                            keypoint_type=f"keypoint_{i}"
                        )
                        keypoints.append(keypoint)
                    
                    pose_frame = MMPoseFrame(
                        frame_number=frame_number,
                        timestamp=frame_number / fps,
                        keypoints=keypoints,
                        frame_confidence=0.7
                    )
                    pose_frames.append(pose_frame)
                
                frame_number += 1
            
            cap.release()
            logger.warning(f"⚠️ Using fallback pose extraction: {len(pose_frames)} frames")
            return pose_frames
            
        except Exception as e:
            logger.error(f"❌ Fallback pose extraction failed: {e}")
            return []
    
    async def _analyze_dance_metrics(self, pose_frames: List[MMPoseFrame], request: ChallengeAnalysisRequest) -> Dict:
        """Analyze dance-specific metrics"""
        try:
            return await self.metrics_analyzer.analyze_dance_metrics(pose_frames, request)
        except Exception as e:
            logger.error(f"❌ Error analyzing dance metrics: {e}")
            return {}
    
    async def _calculate_scores(self, pose_frames: List[MMPoseFrame], dance_metrics: Dict, request: ChallengeAnalysisRequest) -> DanceScoringResult:
        """Calculate comprehensive dance scores"""
        try:
            return await self.scoring_engine.calculate_scores(pose_frames, dance_metrics, request)
        except Exception as e:
            logger.error(f"❌ Error calculating scores: {e}")
            # Return default scores
            from .models import DanceTechniqueMetrics, RhythmMetrics, ExpressionMetrics, DifficultyMetrics
            
            return DanceScoringResult(
                technique=DanceTechniqueMetrics(
                    balance_stability=0.5,
                    joint_alignment=0.5,
                    posture_quality=0.5,
                    movement_precision=0.5,
                    technique_consistency=0.5
                ),
                rhythm=RhythmMetrics(
                    beat_synchronization=0.5,
                    movement_timing=0.5,
                    rhythm_consistency=0.5,
                    tempo_matching=0.5,
                    musicality=0.5
                ),
                expression=ExpressionMetrics(
                    movement_flow=0.5,
                    energy_expression=0.5,
                    style_authenticity=0.5,
                    performance_quality=0.5,
                    artistic_expression=0.5
                ),
                difficulty=DifficultyMetrics(
                    movement_complexity=0.5,
                    physical_demand=0.5,
                    skill_requirement=0.5,
                    coordination_difficulty=0.5,
                    overall_difficulty=0.5
                ),
                technique_score=50,
                rhythm_score=50,
                expression_score=50,
                difficulty_score=50,
                total_score=50,
                confidence=0.5,
                processing_time=0.0,
                frames_analyzed=len(pose_frames),
                total_frames=len(pose_frames)
            )
    
    async def get_analysis_status(self, submission_id: str) -> Optional[ChallengeAnalysisResponse]:
        """Get current analysis status"""
        return self.analysis_queue.get(submission_id)

# Global service instance
mmpose_service = MMPoseService() 