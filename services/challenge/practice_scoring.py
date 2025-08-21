#!/usr/bin/env python3
"""
Practice Scoring Service for Challenge Attempts
Analyzes practice videos against challenge reference without saving practice videos
"""

import os
import tempfile
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import HTTPException, UploadFile
from services.ai.enhanced_scoring import EnhancedDanceScoringService
from services.video_processing.middleware import video_resizing_middleware

logger = logging.getLogger(__name__)

class PracticeScoringService:
    """Service for scoring practice challenge attempts"""
    
    def __init__(self):
        self.scoring_service = EnhancedDanceScoringService()
    
    async def score_practice_attempt(
        self,
        practice_video: UploadFile,
        challenge_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Score a practice attempt against challenge reference
        
        Args:
            practice_video: Uploaded practice video file
            challenge_id: ID of the challenge being practiced
            user_id: ID of the user practicing
            
        Returns:
            Dictionary containing score breakdown and feedback
        """
        try:
            logger.info(f"🎯 Starting practice scoring for user {user_id} on challenge {challenge_id}")
            
            # Get challenge reference video
            challenge_video_url = await self._get_challenge_reference_video(challenge_id)
            if not challenge_video_url:
                raise HTTPException(status_code=404, detail="Challenge reference video not found")
            
            # Save practice video to temporary file
            temp_practice_path = await self._save_practice_video(practice_video)
            
            try:
                # Process practice video through resizing middleware
                processed_practice_path = await video_resizing_middleware.process_video_file(
                    temp_practice_path, cleanup_original=True
                )
                
                # Analyze practice video against challenge reference
                score_result = await self._analyze_practice_attempt(
                    processed_practice_path, 
                    challenge_video_url, 
                    challenge_id,
                    user_id
                )
                
                # Add practice-specific metadata
                score_result.update({
                    "practice_timestamp": datetime.utcnow().isoformat(),
                    "challenge_id": challenge_id,
                    "user_id": user_id,
                    "is_practice": True,
                    "message": "Practice attempt scored successfully"
                })
                
                logger.info(f"✅ Practice scoring completed for user {user_id} on challenge {challenge_id}")
                return score_result
                
            finally:
                # Clean up temporary files
                self._cleanup_temp_files([temp_practice_path, processed_practice_path])
                
        except Exception as e:
            logger.error(f"❌ Error in practice scoring: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Practice scoring failed: {str(e)}")
    
    async def _get_challenge_details(self, challenge_id: str) -> Dict[str, Any]:
        """Get challenge details for scoring"""
        try:
            from infra.mongo import Database
            from bson import ObjectId
            
            db = Database.get_database()
            challenges_collection = Database.get_collection_name('challenges')
            
            challenge = await db[challenges_collection].find_one({'_id': ObjectId(challenge_id)})
            
            if not challenge:
                return {
                    'type': 'general',
                    'difficultyLevel': 'intermediate',
                    'bpm': None
                }
            
            return {
                'type': challenge.get('type', 'general'),
                'difficultyLevel': challenge.get('difficultyLevel', 'intermediate'),
                'bpm': challenge.get('bpm'),
                'title': challenge.get('title', 'Unknown Challenge'),
                'description': challenge.get('description', '')
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting challenge details: {str(e)}")
            return {
                'type': 'general',
                'difficultyLevel': 'intermediate',
                'bpm': None
            }
    
    async def _get_challenge_reference_video(self, challenge_id: str) -> Optional[str]:
        """Get the reference video URL for a challenge"""
        try:
            from infra.mongo import Database
            from bson import ObjectId
            
            db = Database.get_database()
            challenges_collection = Database.get_collection_name('challenges')
            
            challenge = await db[challenges_collection].find_one({'_id': ObjectId(challenge_id)})
            
            if challenge and 'demoVideoFileKey' in challenge:
                # Try to get presigned URL for S3 access
                try:
                    import boto3
                    from botocore.exceptions import ClientError
                    
                    s3_client = boto3.client(
                        's3',
                        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                        region_name=os.getenv('AWS_REGION', 'ap-south-1')
                    )
                    
                    bucket_name = os.getenv('S3_BUCKET_NAME', 'idanceshreyansh')
                    file_key = challenge['demoVideoFileKey']
                    
                    # Generate presigned URL (expires in 1 hour)
                    presigned_url = s3_client.generate_presigned_url(
                        'get_object',
                        Params={'Bucket': bucket_name, 'Key': file_key},
                        ExpiresIn=3600
                    )
                    
                    logger.info(f"✅ Generated presigned URL for reference video: {file_key}")
                    return presigned_url
                    
                except Exception as s3_error:
                    logger.warning(f"⚠️ Could not generate presigned URL: {str(s3_error)}")
                    # Fallback to direct S3 URL
                    bucket_name = os.getenv('S3_BUCKET_NAME', 'idanceshreyansh')
                    return f"https://{bucket_name}.s3.amazonaws.com/{challenge['demoVideoFileKey']}"
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting challenge reference video: {str(e)}")
            return None
    
    async def _save_practice_video(self, practice_video: UploadFile) -> str:
        """Save uploaded practice video to temporary file"""
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            # Save uploaded file
            with open(temp_path, "wb") as buffer:
                content = await practice_video.read()
                buffer.write(content)
            
            logger.info(f"✅ Practice video saved to temporary file: {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"❌ Error saving practice video: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to save practice video")
    
    async def _analyze_practice_attempt(
        self, 
        practice_video_path: str, 
        challenge_video_url: str,
        challenge_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Analyze practice attempt against challenge reference"""
        try:
            # Generate temporary submission ID for practice
            practice_submission_id = f"practice_{user_id}_{challenge_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            # Get challenge details for scoring
            challenge_details = await self._get_challenge_details(challenge_id)
            
            # First, try to analyze with reference video comparison
            if challenge_video_url:
                try:
                    result = await self._analyze_with_reference_comparison(
                        practice_video_path, 
                        challenge_video_url, 
                        challenge_details,
                        practice_submission_id
                    )
                    return result
                except Exception as e:
                    logger.warning(f"⚠️ Reference comparison failed, falling back to standalone analysis: {str(e)}")
            
            # Fallback to standalone analysis
            score_result = await self.scoring_service.analyze_challenge_submission(
                submission_id=practice_submission_id,
                video_url=f"file://{practice_video_path}",  # Local file path
                challenge_type=challenge_details.get('type', 'general'),
                challenge_difficulty=challenge_details.get('difficultyLevel', 'intermediate'),
                target_bpm=challenge_details.get('bpm')
            )
            
            # Convert AnalysisData to dictionary format
            result = {
                "score": score_result.score or 0,
                "breakdown": score_result.breakdown or {
                    "technique": 0,
                    "rhythm": 0,
                    "expression": 0,
                    "difficulty": 0
                },
                "feedback": score_result.feedback or "Analysis completed",
                "overall_rating": self._get_overall_rating(score_result.score or 0),
                "improvement_suggestions": self._generate_improvement_suggestions(score_result),
                "practice_metrics": {
                    "video_duration": await self._get_video_duration(practice_video_path),
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                    "analysis_type": "standalone"
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error analyzing practice attempt: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to analyze practice attempt")
    
    async def _analyze_with_reference_comparison(
        self, 
        practice_video_path: str, 
        challenge_video_url: str,
        challenge_details: Dict[str, Any],
        practice_submission_id: str
    ) -> Dict[str, Any]:
        """Analyze practice video with reference video comparison"""
        try:
            logger.info(f"🎯 Starting reference comparison analysis for {practice_submission_id}")
            
            # Import video analysis service
            from services.ai.video_analysis import VideoAnalysisService
            
            video_analyzer = VideoAnalysisService()
            
            # Analyze practice video
            practice_result = await video_analyzer.analyze_video(
                f"file://{practice_video_path}", 
                f"{practice_submission_id}_practice"
            )
            
            if not practice_result or not practice_result.pose_frames:
                raise Exception("Failed to analyze practice video")
            
            # Try to analyze reference video (handle S3 access issues)
            reference_result = None
            try:
                reference_result = await video_analyzer.analyze_video(
                    challenge_video_url, 
                    f"{practice_submission_id}_reference"
                )
            except Exception as e:
                logger.warning(f"⚠️ Could not analyze reference video: {str(e)}")
                logger.info("🔄 Falling back to practice-only analysis with enhanced scoring")
            
            if reference_result and reference_result.pose_frames:
                # Full comparison analysis
                comparison_scores = self._compare_videos(
                    practice_result.pose_frames,
                    reference_result.pose_frames,
                    challenge_details
                )
                
                # Generate comparison-based feedback
                feedback = self._generate_comparison_feedback(comparison_scores, challenge_details)
                
                result = {
                    "score": comparison_scores["total_score"],
                    "breakdown": comparison_scores["breakdown"],
                    "feedback": feedback,
                    "overall_rating": self._get_overall_rating(comparison_scores["total_score"]),
                    "improvement_suggestions": self._generate_comparison_suggestions(comparison_scores),
                    "practice_metrics": {
                        "video_duration": await self._get_video_duration(practice_video_path),
                        "analysis_timestamp": datetime.utcnow().isoformat(),
                        "analysis_type": "reference_comparison",
                        "reference_video_analyzed": True
                    }
                }
            else:
                # Enhanced practice-only analysis
                enhanced_scores = self._analyze_practice_enhanced(
                    practice_result.pose_frames,
                    challenge_details
                )
                
                feedback = self._generate_enhanced_practice_feedback(enhanced_scores, challenge_details)
                
                result = {
                    "score": enhanced_scores["total_score"],
                    "breakdown": enhanced_scores["breakdown"],
                    "feedback": feedback,
                    "overall_rating": self._get_overall_rating(enhanced_scores["total_score"]),
                    "improvement_suggestions": self._generate_enhanced_practice_suggestions(enhanced_scores),
                    "practice_metrics": {
                        "video_duration": await self._get_video_duration(practice_video_path),
                        "analysis_timestamp": datetime.utcnow().isoformat(),
                        "analysis_type": "enhanced_practice_only",
                        "reference_video_analyzed": False
                    }
                }
            
            logger.info(f"✅ Analysis completed for {practice_submission_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in reference comparison analysis: {str(e)}")
            raise
    
    def _get_overall_rating(self, score: int) -> str:
        """Get overall rating based on score"""
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Very Good"
        elif score >= 70:
            return "Good"
        elif score >= 60:
            return "Fair"
        else:
            return "Poor"
    
    def _compare_videos(
        self, 
        practice_frames: List, 
        reference_frames: List, 
        challenge_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare practice video with reference video"""
        try:
            # Calculate basic metrics for both videos
            practice_metrics = self._calculate_video_metrics(practice_frames)
            reference_metrics = self._calculate_video_metrics(reference_frames)
            
            # Compare movement patterns
            movement_similarity = self._calculate_movement_similarity(practice_frames, reference_frames)
            
            # Calculate scores based on comparison
            technique_score = self._calculate_technique_comparison(practice_metrics, reference_metrics, movement_similarity)
            rhythm_score = self._calculate_rhythm_comparison(practice_metrics, reference_metrics, challenge_details.get('bpm'))
            expression_score = self._calculate_expression_comparison(practice_metrics, reference_metrics)
            difficulty_score = self._calculate_difficulty_comparison(practice_metrics, reference_metrics, challenge_details.get('difficultyLevel'))
            
            # Calculate total score
            total_score = int((technique_score + rhythm_score + expression_score + difficulty_score) / 4)
            
            return {
                "total_score": total_score,
                "breakdown": {
                    "technique": technique_score,
                    "rhythm": rhythm_score,
                    "expression": expression_score,
                    "difficulty": difficulty_score
                },
                "comparison_metrics": {
                    "movement_similarity": movement_similarity,
                    "practice_metrics": practice_metrics,
                    "reference_metrics": reference_metrics
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error comparing videos: {str(e)}")
            return {
                "total_score": 50,
                "breakdown": {
                    "technique": 50,
                    "rhythm": 50,
                    "expression": 50,
                    "difficulty": 50
                }
            }
    
    def _calculate_video_metrics(self, frames: List) -> Dict[str, Any]:
        """Calculate basic metrics for a video"""
        try:
            if not frames:
                return {}
            
            valid_frames = [f for f in frames if f.frame_confidence > 0.5]
            
            if len(valid_frames) < 5:
                return {}
            
            # Calculate movement intensity
            movement_intensity = self._calculate_movement_intensity(valid_frames)
            
            # Calculate pose stability
            pose_stability = self._calculate_pose_stability(valid_frames)
            
            # Calculate rhythm consistency
            rhythm_consistency = self._calculate_rhythm_consistency(valid_frames)
            
            return {
                "movement_intensity": movement_intensity,
                "pose_stability": pose_stability,
                "rhythm_consistency": rhythm_consistency,
                "total_frames": len(frames),
                "valid_frames": len(valid_frames)
            }
            
        except Exception as e:
            logger.error(f"❌ Error calculating video metrics: {str(e)}")
            return {}
    
    def _calculate_movement_intensity(self, frames: List) -> float:
        """Calculate movement intensity based on pose changes"""
        try:
            if len(frames) < 2:
                return 0.0
            
            total_movement = 0.0
            for i in range(1, len(frames)):
                prev_frame = frames[i-1]
                curr_frame = frames[i]
                
                # Calculate movement between consecutive frames
                frame_movement = self._calculate_frame_movement(prev_frame, curr_frame)
                total_movement += frame_movement
            
            return total_movement / (len(frames) - 1)
            
        except Exception as e:
            logger.error(f"❌ Error calculating movement intensity: {str(e)}")
            return 0.0
    
    def _calculate_frame_movement(self, frame1, frame2) -> float:
        """Calculate movement between two frames"""
        try:
            if not frame1.keypoints or not frame2.keypoints:
                return 0.0
            
            total_movement = 0.0
            valid_points = 0
            
            # Compare keypoints between frames
            for i, (kp1, kp2) in enumerate(zip(frame1.keypoints, frame2.keypoints)):
                if kp1.confidence > 0.5 and kp2.confidence > 0.5:
                    # Calculate Euclidean distance between keypoints
                    distance = ((kp1.x - kp2.x) ** 2 + (kp1.y - kp2.y) ** 2) ** 0.5
                    total_movement += distance
                    valid_points += 1
            
            return total_movement / valid_points if valid_points > 0 else 0.0
            
        except Exception as e:
            logger.error(f"❌ Error calculating frame movement: {str(e)}")
            return 0.0
    
    def _calculate_pose_stability(self, frames: List) -> float:
        """Calculate pose stability"""
        try:
            if len(frames) < 5:
                return 0.0
            
            # Calculate variance in keypoint positions
            stability_scores = []
            for i in range(1, len(frames)):
                stability = self._calculate_frame_stability(frames[i-1], frames[i])
                stability_scores.append(stability)
            
            return sum(stability_scores) / len(stability_scores) if stability_scores else 0.0
            
        except Exception as e:
            logger.error(f"❌ Error calculating pose stability: {str(e)}")
            return 0.0
    
    def _calculate_frame_stability(self, frame1, frame2) -> float:
        """Calculate stability between two frames"""
        try:
            if not frame1.keypoints or not frame2.keypoints:
                return 0.0
            
            # Calculate how much keypoints have moved
            total_movement = 0.0
            valid_points = 0
            
            for kp1, kp2 in zip(frame1.keypoints, frame2.keypoints):
                if kp1.confidence > 0.5 and kp2.confidence > 0.5:
                    distance = ((kp1.x - kp2.x) ** 2 + (kp1.y - kp2.y) ** 2) ** 0.5
                    total_movement += distance
                    valid_points += 1
            
            # Lower movement = higher stability
            if valid_points > 0:
                avg_movement = total_movement / valid_points
                stability = max(0, 1 - avg_movement)  # Normalize to 0-1
                return stability
            
            return 0.0
            
        except Exception as e:
            logger.error(f"❌ Error calculating frame stability: {str(e)}")
            return 0.0
    
    def _calculate_rhythm_consistency(self, frames: List) -> float:
        """Calculate rhythm consistency"""
        try:
            if len(frames) < 10:
                return 0.0
            
            # Analyze timing patterns
            timestamps = [frame.timestamp for frame in frames if frame.timestamp is not None]
            
            if len(timestamps) < 5:
                return 0.0
            
            # Calculate time intervals between frames
            intervals = []
            for i in range(1, len(timestamps)):
                interval = timestamps[i] - timestamps[i-1]
                if interval > 0:
                    intervals.append(interval)
            
            if len(intervals) < 3:
                return 0.0
            
            # Calculate consistency (lower variance = higher consistency)
            mean_interval = sum(intervals) / len(intervals)
            variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
            
            # Normalize to 0-1 (lower variance = higher consistency)
            consistency = max(0, 1 - (variance / (mean_interval ** 2)))
            return consistency
            
        except Exception as e:
            logger.error(f"❌ Error calculating rhythm consistency: {str(e)}")
            return 0.0
    
    def _calculate_movement_similarity(self, practice_frames: List, reference_frames: List) -> float:
        """Calculate similarity between practice and reference movements"""
        try:
            # Simple similarity calculation based on movement patterns
            practice_metrics = self._calculate_video_metrics(practice_frames)
            reference_metrics = self._calculate_video_metrics(reference_frames)
            
            if not practice_metrics or not reference_metrics:
                return 0.5
            
            # Compare movement intensity
            intensity_diff = abs(practice_metrics.get('movement_intensity', 0) - reference_metrics.get('movement_intensity', 0))
            intensity_similarity = max(0, 1 - (intensity_diff / max(practice_metrics.get('movement_intensity', 1), reference_metrics.get('movement_intensity', 1), 1)))
            
            # Compare pose stability
            stability_diff = abs(practice_metrics.get('pose_stability', 0) - reference_metrics.get('pose_stability', 0))
            stability_similarity = max(0, 1 - stability_diff)
            
            # Average similarity
            return (intensity_similarity + stability_similarity) / 2
            
        except Exception as e:
            logger.error(f"❌ Error calculating movement similarity: {str(e)}")
            return 0.5
    
    def _calculate_technique_comparison(self, practice_metrics: Dict, reference_metrics: Dict, movement_similarity: float) -> int:
        """Calculate technique score based on comparison"""
        try:
            base_score = 50
            
            # Pose stability comparison
            if practice_metrics.get('pose_stability', 0) > 0.7:
                base_score += 20
            elif practice_metrics.get('pose_stability', 0) > 0.5:
                base_score += 10
            
            # Movement similarity bonus
            similarity_bonus = int(movement_similarity * 20)
            base_score += similarity_bonus
            
            return min(100, max(0, base_score))
            
        except Exception as e:
            logger.error(f"❌ Error calculating technique comparison: {str(e)}")
            return 50
    
    def _calculate_rhythm_comparison(self, practice_metrics: Dict, reference_metrics: Dict, target_bpm: Optional[int]) -> int:
        """Calculate rhythm score based on comparison"""
        try:
            base_score = 50
            
            # Rhythm consistency
            rhythm_consistency = practice_metrics.get('rhythm_consistency', 0)
            if rhythm_consistency > 0.8:
                base_score += 25
            elif rhythm_consistency > 0.6:
                base_score += 15
            elif rhythm_consistency > 0.4:
                base_score += 5
            
            # BPM matching (if available)
            if target_bpm and practice_metrics.get('movement_intensity', 0) > 0:
                # Simple BPM estimation based on movement intensity
                estimated_bpm = practice_metrics['movement_intensity'] * 120  # Rough estimation
                bpm_diff = abs(estimated_bpm - target_bpm)
                if bpm_diff < 10:
                    base_score += 15
                elif bpm_diff < 20:
                    base_score += 10
                elif bpm_diff < 30:
                    base_score += 5
            
            return min(100, max(0, base_score))
            
        except Exception as e:
            logger.error(f"❌ Error calculating rhythm comparison: {str(e)}")
            return 50
    
    def _calculate_expression_comparison(self, practice_metrics: Dict, reference_metrics: Dict) -> int:
        """Calculate expression score based on comparison"""
        try:
            base_score = 50
            
            # Movement intensity (higher = more expressive)
            movement_intensity = practice_metrics.get('movement_intensity', 0)
            if movement_intensity > 0.8:
                base_score += 25
            elif movement_intensity > 0.6:
                base_score += 15
            elif movement_intensity > 0.4:
                base_score += 10
            
            # Pose stability (good form)
            pose_stability = practice_metrics.get('pose_stability', 0)
            if pose_stability > 0.7:
                base_score += 10
            
            return min(100, max(0, base_score))
            
        except Exception as e:
            logger.error(f"❌ Error calculating expression comparison: {str(e)}")
            return 50
    
    def _calculate_difficulty_comparison(self, practice_metrics: Dict, reference_metrics: Dict, difficulty_level: str) -> int:
        """Calculate difficulty score based on comparison"""
        try:
            base_score = 50
            
            # Movement intensity (higher = more difficult)
            movement_intensity = practice_metrics.get('movement_intensity', 0)
            
            if difficulty_level == 'beginner':
                if movement_intensity > 0.6:
                    base_score += 20
                elif movement_intensity > 0.4:
                    base_score += 10
            elif difficulty_level == 'intermediate':
                if movement_intensity > 0.7:
                    base_score += 20
                elif movement_intensity > 0.5:
                    base_score += 10
            elif difficulty_level == 'advanced':
                if movement_intensity > 0.8:
                    base_score += 25
                elif movement_intensity > 0.6:
                    base_score += 15
            
            return min(100, max(0, base_score))
            
        except Exception as e:
            logger.error(f"❌ Error calculating difficulty comparison: {str(e)}")
            return 50
    
    def _generate_comparison_feedback(self, comparison_scores: Dict, challenge_details: Dict) -> str:
        """Generate feedback based on video comparison"""
        try:
            feedback_parts = []
            
            total_score = comparison_scores.get('total_score', 50)
            breakdown = comparison_scores.get('breakdown', {})
            similarity = comparison_scores.get('comparison_metrics', {}).get('movement_similarity', 0.5)
            
            # Overall performance
            if total_score >= 80:
                feedback_parts.append("Excellent performance! You're very close to the reference video.")
            elif total_score >= 70:
                feedback_parts.append("Great job! You're following the reference well with some room for improvement.")
            elif total_score >= 60:
                feedback_parts.append("Good effort! Focus on matching the reference video more closely.")
            else:
                feedback_parts.append("Keep practicing! Try to match the reference video more closely.")
            
            # Movement similarity
            if similarity >= 0.8:
                feedback_parts.append("Your movement patterns closely match the reference!")
            elif similarity >= 0.6:
                feedback_parts.append("Your movements are similar to the reference, keep refining.")
            else:
                feedback_parts.append("Try to match the movement patterns in the reference video more closely.")
            
            # Specific feedback based on scores
            technique = breakdown.get('technique', 50)
            if technique < 70:
                feedback_parts.append("Focus on maintaining better form and stability.")
            
            rhythm = breakdown.get('rhythm', 50)
            if rhythm < 70:
                feedback_parts.append("Work on timing and rhythm consistency.")
            
            expression = breakdown.get('expression', 50)
            if expression < 70:
                feedback_parts.append("Add more energy and expression to your performance.")
            
            difficulty = breakdown.get('difficulty', 50)
            if difficulty < 70:
                feedback_parts.append("Challenge yourself with more complex movements.")
            
            return " ".join(feedback_parts)
            
        except Exception as e:
            logger.error(f"❌ Error generating comparison feedback: {str(e)}")
            return "Great effort! Keep practicing and improving your dance skills."
    
    def _analyze_practice_enhanced(self, practice_frames: List, challenge_details: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced analysis of practice video without reference comparison (handles speed variations)"""
        try:
            # Calculate comprehensive metrics for practice video
            practice_metrics = self._calculate_enhanced_practice_metrics(practice_frames)
            
            # Calculate scores based on practice performance (not comparison)
            technique_score = self._calculate_technique_practice_only(practice_metrics)
            rhythm_score = self._calculate_rhythm_practice_only(practice_metrics, challenge_details.get('bpm'))
            expression_score = self._calculate_expression_practice_only(practice_metrics)
            difficulty_score = self._calculate_difficulty_practice_only(practice_metrics, challenge_details.get('difficultyLevel'))
            
            # Calculate total score
            total_score = int((technique_score + rhythm_score + expression_score + difficulty_score) / 4)
            
            return {
                "total_score": total_score,
                "breakdown": {
                    "technique": technique_score,
                    "rhythm": rhythm_score,
                    "expression": expression_score,
                    "difficulty": difficulty_score
                },
                "practice_metrics": practice_metrics
            }
            
        except Exception as e:
            logger.error(f"❌ Error in enhanced practice analysis: {str(e)}")
            return {
                "total_score": 50,
                "breakdown": {
                    "technique": 50,
                    "rhythm": 50,
                    "expression": 50,
                    "difficulty": 50
                }
            }
    
    def _calculate_enhanced_practice_metrics(self, frames: List) -> Dict[str, Any]:
        """Calculate enhanced metrics for practice video (speed-invariant)"""
        try:
            if not frames:
                return {}
            
            valid_frames = [f for f in frames if f.frame_confidence > 0.5]
            
            if len(valid_frames) < 5:
                return {}
            
            # Speed-invariant metrics
            movement_quality = self._calculate_movement_quality(valid_frames)
            pose_consistency = self._calculate_pose_consistency(valid_frames)
            movement_complexity = self._calculate_movement_complexity(valid_frames)
            energy_level = self._calculate_energy_level(valid_frames)
            
            # Timing analysis (relative to video duration, not absolute time)
            timing_consistency = self._calculate_timing_consistency(valid_frames)
            
            return {
                "movement_quality": movement_quality,
                "pose_consistency": pose_consistency,
                "movement_complexity": movement_complexity,
                "energy_level": energy_level,
                "timing_consistency": timing_consistency,
                "total_frames": len(frames),
                "valid_frames": len(valid_frames),
                "video_duration": frames[-1].timestamp if frames else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error calculating enhanced practice metrics: {str(e)}")
            return {}
    
    def _calculate_movement_quality(self, frames: List) -> float:
        """Calculate movement quality (smoothness, control) - speed invariant"""
        try:
            if len(frames) < 3:
                return 0.0
            
            smoothness_scores = []
            for i in range(1, len(frames) - 1):
                # Calculate smoothness between consecutive frames
                prev_frame = frames[i-1]
                curr_frame = frames[i]
                next_frame = frames[i+1]
                
                # Check for smooth transitions
                prev_movement = self._calculate_frame_movement(prev_frame, curr_frame)
                next_movement = self._calculate_frame_movement(curr_frame, next_frame)
                
                # Smoothness = consistency of movement magnitude
                movement_diff = abs(prev_movement - next_movement)
                smoothness = max(0, 1 - (movement_diff / max(prev_movement, next_movement, 0.1)))
                smoothness_scores.append(smoothness)
            
            return sum(smoothness_scores) / len(smoothness_scores) if smoothness_scores else 0.0
            
        except Exception as e:
            logger.error(f"❌ Error calculating movement quality: {str(e)}")
            return 0.0
    
    def _calculate_pose_consistency(self, frames: List) -> float:
        """Calculate pose consistency (how well poses are maintained)"""
        try:
            if len(frames) < 5:
                return 0.0
            
            consistency_scores = []
            for i in range(1, len(frames)):
                prev_frame = frames[i-1]
                curr_frame = frames[i]
                
                # Calculate pose similarity between consecutive frames
                pose_similarity = self._calculate_pose_similarity(prev_frame, curr_frame)
                consistency_scores.append(pose_similarity)
            
            return sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.0
            
        except Exception as e:
            logger.error(f"❌ Error calculating pose consistency: {str(e)}")
            return 0.0
    
    def _calculate_pose_similarity(self, frame1, frame2) -> float:
        """Calculate similarity between two poses"""
        try:
            if not frame1.keypoints or not frame2.keypoints:
                return 0.0
            
            total_similarity = 0.0
            valid_points = 0
            
            for kp1, kp2 in zip(frame1.keypoints, frame2.keypoints):
                if kp1.confidence > 0.5 and kp2.confidence > 0.5:
                    # Calculate similarity based on position
                    distance = ((kp1.x - kp2.x) ** 2 + (kp1.y - kp2.y) ** 2) ** 0.5
                    similarity = max(0, 1 - distance)  # Closer = more similar
                    total_similarity += similarity
                    valid_points += 1
            
            return total_similarity / valid_points if valid_points > 0 else 0.0
            
        except Exception as e:
            logger.error(f"❌ Error calculating pose similarity: {str(e)}")
            return 0.0
    
    def _calculate_movement_complexity(self, frames: List) -> float:
        """Calculate movement complexity (variety of movements)"""
        try:
            if len(frames) < 10:
                return 0.0
            
            # Analyze movement patterns
            movement_patterns = []
            for i in range(1, len(frames)):
                movement = self._calculate_frame_movement(frames[i-1], frames[i])
                movement_patterns.append(movement)
            
            # Calculate complexity based on movement variety
            unique_movements = len(set([round(m, 2) for m in movement_patterns]))
            complexity = min(1.0, unique_movements / len(movement_patterns))
            
            return complexity
            
        except Exception as e:
            logger.error(f"❌ Error calculating movement complexity: {str(e)}")
            return 0.0
    
    def _calculate_energy_level(self, frames: List) -> float:
        """Calculate energy level based on movement intensity"""
        try:
            if len(frames) < 5:
                return 0.0
            
            total_energy = 0.0
            for i in range(1, len(frames)):
                movement = self._calculate_frame_movement(frames[i-1], frames[i])
                total_energy += movement
            
            avg_energy = total_energy / (len(frames) - 1)
            # Normalize to 0-1 range
            return min(1.0, avg_energy / 0.1)  # Assuming 0.1 is high energy threshold
            
        except Exception as e:
            logger.error(f"❌ Error calculating energy level: {str(e)}")
            return 0.0
    
    def _calculate_timing_consistency(self, frames: List) -> float:
        """Calculate timing consistency (relative to video duration)"""
        try:
            if len(frames) < 10:
                return 0.0
            
            # Calculate relative timestamps (0-1 range)
            total_duration = frames[-1].timestamp - frames[0].timestamp
            if total_duration <= 0:
                return 0.0
            
            relative_timestamps = [(f.timestamp - frames[0].timestamp) / total_duration for f in frames]
            
            # Calculate intervals between relative timestamps
            intervals = []
            for i in range(1, len(relative_timestamps)):
                interval = relative_timestamps[i] - relative_timestamps[i-1]
                if interval > 0:
                    intervals.append(interval)
            
            if len(intervals) < 3:
                return 0.0
            
            # Calculate consistency (lower variance = higher consistency)
            mean_interval = sum(intervals) / len(intervals)
            variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
            
            # Normalize to 0-1 (lower variance = higher consistency)
            consistency = max(0, 1 - (variance / (mean_interval ** 2)))
            return consistency
            
        except Exception as e:
            logger.error(f"❌ Error calculating timing consistency: {str(e)}")
            return 0.0
    
    def _calculate_technique_practice_only(self, practice_metrics: Dict) -> int:
        """Calculate technique score for practice-only analysis"""
        try:
            base_score = 50
            
            # Movement quality
            movement_quality = practice_metrics.get('movement_quality', 0)
            if movement_quality > 0.8:
                base_score += 25
            elif movement_quality > 0.6:
                base_score += 15
            elif movement_quality > 0.4:
                base_score += 10
            
            # Pose consistency
            pose_consistency = practice_metrics.get('pose_consistency', 0)
            if pose_consistency > 0.7:
                base_score += 15
            
            return min(100, max(0, base_score))
            
        except Exception as e:
            logger.error(f"❌ Error calculating technique practice-only: {str(e)}")
            return 50
    
    def _calculate_rhythm_practice_only(self, practice_metrics: Dict, target_bpm: Optional[int]) -> int:
        """Calculate rhythm score for practice-only analysis"""
        try:
            base_score = 50
            
            # Timing consistency
            timing_consistency = practice_metrics.get('timing_consistency', 0)
            if timing_consistency > 0.8:
                base_score += 30
            elif timing_consistency > 0.6:
                base_score += 20
            elif timing_consistency > 0.4:
                base_score += 10
            
            # Energy level (indicates rhythm engagement)
            energy_level = practice_metrics.get('energy_level', 0)
            if energy_level > 0.7:
                base_score += 10
            
            return min(100, max(0, base_score))
            
        except Exception as e:
            logger.error(f"❌ Error calculating rhythm practice-only: {str(e)}")
            return 50
    
    def _calculate_expression_practice_only(self, practice_metrics: Dict) -> int:
        """Calculate expression score for practice-only analysis"""
        try:
            base_score = 50
            
            # Energy level
            energy_level = practice_metrics.get('energy_level', 0)
            if energy_level > 0.8:
                base_score += 30
            elif energy_level > 0.6:
                base_score += 20
            elif energy_level > 0.4:
                base_score += 10
            
            # Movement complexity (more complex = more expressive)
            movement_complexity = practice_metrics.get('movement_complexity', 0)
            if movement_complexity > 0.7:
                base_score += 15
            
            return min(100, max(0, base_score))
            
        except Exception as e:
            logger.error(f"❌ Error calculating expression practice-only: {str(e)}")
            return 50
    
    def _calculate_difficulty_practice_only(self, practice_metrics: Dict, difficulty_level: str) -> int:
        """Calculate difficulty score for practice-only analysis"""
        try:
            base_score = 50
            
            # Movement complexity
            movement_complexity = practice_metrics.get('movement_complexity', 0)
            energy_level = practice_metrics.get('energy_level', 0)
            
            if difficulty_level == 'beginner':
                if movement_complexity > 0.5 and energy_level > 0.5:
                    base_score += 25
                elif movement_complexity > 0.3 or energy_level > 0.3:
                    base_score += 15
            elif difficulty_level == 'intermediate':
                if movement_complexity > 0.6 and energy_level > 0.6:
                    base_score += 25
                elif movement_complexity > 0.4 or energy_level > 0.4:
                    base_score += 15
            elif difficulty_level == 'advanced':
                if movement_complexity > 0.7 and energy_level > 0.7:
                    base_score += 30
                elif movement_complexity > 0.5 or energy_level > 0.5:
                    base_score += 20
            
            return min(100, max(0, base_score))
            
        except Exception as e:
            logger.error(f"❌ Error calculating difficulty practice-only: {str(e)}")
            return 50
    
    def _generate_enhanced_practice_feedback(self, enhanced_scores: Dict, challenge_details: Dict) -> str:
        """Generate feedback for enhanced practice-only analysis"""
        try:
            feedback_parts = []
            
            total_score = enhanced_scores.get('total_score', 50)
            breakdown = enhanced_scores.get('breakdown', {})
            metrics = enhanced_scores.get('practice_metrics', {})
            
            # Overall performance
            if total_score >= 80:
                feedback_parts.append("Excellent practice session! Your movements are smooth and controlled.")
            elif total_score >= 70:
                feedback_parts.append("Great practice! You're showing good form and consistency.")
            elif total_score >= 60:
                feedback_parts.append("Good practice session! Focus on refining your movements.")
            else:
                feedback_parts.append("Keep practicing! Focus on improving your form and consistency.")
            
            # Specific feedback based on metrics
            movement_quality = metrics.get('movement_quality', 0)
            if movement_quality < 0.6:
                feedback_parts.append("Work on making your movements smoother and more controlled.")
            
            pose_consistency = metrics.get('pose_consistency', 0)
            if pose_consistency < 0.6:
                feedback_parts.append("Focus on maintaining consistent poses and form.")
            
            energy_level = metrics.get('energy_level', 0)
            if energy_level < 0.5:
                feedback_parts.append("Add more energy and enthusiasm to your performance.")
            
            timing_consistency = metrics.get('timing_consistency', 0)
            if timing_consistency < 0.6:
                feedback_parts.append("Work on maintaining consistent timing throughout your routine.")
            
            return " ".join(feedback_parts)
            
        except Exception as e:
            logger.error(f"❌ Error generating enhanced practice feedback: {str(e)}")
            return "Great effort! Keep practicing and improving your dance skills."
    
    def _generate_enhanced_practice_suggestions(self, enhanced_scores: Dict) -> list:
        """Generate improvement suggestions for enhanced practice-only analysis"""
        suggestions = []
        
        breakdown = enhanced_scores.get('breakdown', {})
        metrics = enhanced_scores.get('practice_metrics', {})
        
        # Technique suggestions
        technique = breakdown.get('technique', 50)
        if technique < 70:
            suggestions.append("Focus on smoother, more controlled movements")
        
        # Rhythm suggestions
        rhythm = breakdown.get('rhythm', 50)
        if rhythm < 70:
            suggestions.append("Work on maintaining consistent timing throughout your routine")
        
        # Expression suggestions
        expression = breakdown.get('expression', 50)
        if expression < 70:
            suggestions.append("Add more energy and enthusiasm to your performance")
        
        # Difficulty suggestions
        difficulty = breakdown.get('difficulty', 50)
        if difficulty < 70:
            suggestions.append("Try incorporating more complex movements and combinations")
        
        # General suggestions
        if len(suggestions) == 0:
            suggestions.append("Excellent practice session! Keep up the great work")
        else:
            suggestions.append("Practice the routine multiple times to improve consistency")
        
        return suggestions
    
    def _generate_comparison_suggestions(self, comparison_scores: Dict) -> list:
        """Generate improvement suggestions based on comparison"""
        suggestions = []
        
        breakdown = comparison_scores.get('breakdown', {})
        similarity = comparison_scores.get('comparison_metrics', {}).get('movement_similarity', 0.5)
        
        # Movement similarity suggestions
        if similarity < 0.6:
            suggestions.append("Watch the reference video more carefully and try to match the movements exactly")
        
        # Technique suggestions
        technique = breakdown.get('technique', 50)
        if technique < 70:
            suggestions.append("Focus on maintaining better balance and body control")
        
        # Rhythm suggestions
        rhythm = breakdown.get('rhythm', 50)
        if rhythm < 70:
            suggestions.append("Practice with the music to improve your timing and rhythm")
        
        # Expression suggestions
        expression = breakdown.get('expression', 50)
        if expression < 70:
            suggestions.append("Add more energy and facial expressions to match the reference performance")
        
        # Difficulty suggestions
        difficulty = breakdown.get('difficulty', 50)
        if difficulty < 70:
            suggestions.append("Try to match the complexity and intensity of the reference video")
        
        # General suggestions
        if len(suggestions) == 0:
            suggestions.append("Excellent work! You're very close to the reference performance")
        else:
            suggestions.append("Practice the routine multiple times to improve consistency")
        
        return suggestions
    
    def _generate_improvement_suggestions(self, score_result) -> list:
        """Generate improvement suggestions based on score breakdown"""
        suggestions = []
        
        breakdown = score_result.breakdown or {}
        score = score_result.score or 0
        
        # Technique suggestions
        if breakdown.get('technique', 0) < 70:
            suggestions.append("Focus on cleaner movement execution and body control")
        
        # Rhythm suggestions
        if breakdown.get('rhythm', 0) < 70:
            suggestions.append("Work on timing and beat synchronization")
        
        # Expression suggestions
        if breakdown.get('expression', 0) < 70:
            suggestions.append("Add more energy and facial expressions to your performance")
        
        # Difficulty suggestions
        if breakdown.get('difficulty', 0) < 70:
            suggestions.append("Try incorporating more complex moves and transitions")
        
        # Overall suggestions
        if score < 70:
            suggestions.append("Practice the routine multiple times to improve consistency")
        elif score < 85:
            suggestions.append("Great progress! Focus on refining the details")
        else:
            suggestions.append("Excellent performance! Ready for final submission")
        
        return suggestions
    
    async def _get_video_duration(self, video_path: str) -> float:
        """Get video duration using ffprobe"""
        try:
            import subprocess
            
            cmd = [
                'ffprobe', 
                '-v', 'quiet', 
                '-show_entries', 'format=duration', 
                '-of', 'csv=p=0', 
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return float(result.stdout.strip())
            else:
                return 0.0
                
        except Exception as e:
            logger.warning(f"⚠️ Could not get video duration: {str(e)}")
            return 0.0
    
    def _cleanup_temp_files(self, file_paths: list):
        """Clean up temporary files"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    logger.debug(f"🧹 Cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to cleanup {file_path}: {str(e)}")

# Global service instance
practice_scoring_service = PracticeScoringService() 