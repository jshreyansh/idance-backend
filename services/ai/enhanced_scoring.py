#!/usr/bin/env python3
"""
Enhanced Dance Scoring Service using MediaPipe with MMPose-style algorithms
"""

import asyncio
import logging
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime

from .models import PoseFrame, PoseKeypoint, PoseAnalysisResult, ScoreBreakdown
from services.challenge.models import AnalysisData

logger = logging.getLogger(__name__)

class EnhancedDanceScoringService:
    """Enhanced dance scoring service using MediaPipe with improved algorithms"""
    
    def __init__(self):
        self.scoring_queue = {}
    
    async def analyze_challenge_submission(self, submission_id: str, video_url: str, 
                                         challenge_type: str, challenge_difficulty: str,
                                         target_bpm: Optional[int] = None) -> AnalysisData:
        """Analyze a challenge submission with enhanced scoring"""
        try:
            logger.info(f"🎯 Starting enhanced dance analysis for submission {submission_id}")
            
            # Import existing MediaPipe service
            from .pose_analysis import pose_analysis_service
            from .video_analysis import VideoAnalysisService
            
            # Use existing MediaPipe analysis
            video_analyzer = VideoAnalysisService()
            pose_result = await video_analyzer.analyze_video(video_url, submission_id)
            
            if not pose_result or not pose_result.pose_frames:
                logger.error(f"❌ No pose data available for submission {submission_id}")
                return self._get_fallback_analysis_data(submission_id, "No pose data available")
            
            # Apply enhanced scoring algorithms
            enhanced_scores = self._calculate_enhanced_scores(
                pose_result.pose_frames, 
                challenge_type, 
                challenge_difficulty, 
                target_bpm
            )
            
            # Generate detailed feedback
            feedback = self._generate_enhanced_feedback(enhanced_scores, challenge_type)
            
            # Create analysis data
            analysis_data = AnalysisData(
                status="completed",
                score=enhanced_scores["total_score"],
                breakdown=enhanced_scores["breakdown"],
                feedback=feedback,
                confidence=enhanced_scores["confidence"]
            )
            
            logger.info(f"✅ Enhanced analysis completed for submission {submission_id}")
            return analysis_data
            
        except Exception as e:
            logger.error(f"❌ Error in enhanced challenge analysis: {e}")
            return self._get_fallback_analysis_data(submission_id, str(e))
    
    def _calculate_enhanced_scores(self, pose_frames: List[PoseFrame], challenge_type: str, 
                                 challenge_difficulty: str, target_bpm: Optional[int]) -> Dict:
        """Calculate enhanced scores using improved algorithms"""
        try:
            # Filter valid frames
            valid_frames = [f for f in pose_frames if f.frame_confidence > 0.5]
            
            if len(valid_frames) < 10:
                logger.warning(f"⚠️ Insufficient valid frames: {len(valid_frames)}")
                return self._get_default_scores()
            
            # Calculate 4-dimensional scores
            technique_score = self._calculate_technique_score(valid_frames)
            rhythm_score = self._calculate_rhythm_score(valid_frames, target_bpm)
            expression_score = self._calculate_expression_score(valid_frames)
            difficulty_score = self._calculate_difficulty_score(valid_frames, challenge_difficulty)
            
            # Calculate total score with challenge-specific weights
            total_score = self._calculate_total_score(
                technique_score, rhythm_score, expression_score, difficulty_score, challenge_type
            )
            
            # Calculate confidence
            confidence = self._calculate_analysis_confidence(valid_frames, pose_frames)
            
            return {
                "technique_score": technique_score,
                "rhythm_score": rhythm_score,
                "expression_score": expression_score,
                "difficulty_score": difficulty_score,
                "total_score": total_score,
                "confidence": confidence,
                "breakdown": {
                    "technique": technique_score,
                    "rhythm": rhythm_score,
                    "expression": expression_score,
                    "difficulty": difficulty_score
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error calculating enhanced scores: {e}")
            return self._get_default_scores()
    
    def _calculate_technique_score(self, frames: List[PoseFrame]) -> int:
        """Calculate technique score (0-100)"""
        try:
            # Balance stability
            balance_stability = self._analyze_balance_stability(frames)
            
            # Joint alignment
            joint_alignment = self._analyze_joint_alignment(frames)
            
            # Posture quality
            posture_quality = self._analyze_posture_quality(frames)
            
            # Movement precision
            movement_precision = self._analyze_movement_precision(frames)
            
            # Technique consistency
            technique_consistency = self._analyze_technique_consistency(frames)
            
            # Calculate overall technique score
            technique_metrics = [
                balance_stability, joint_alignment, posture_quality,
                movement_precision, technique_consistency
            ]
            
            technique_score = int(np.mean(technique_metrics) * 100)
            return max(0, min(100, technique_score))
            
        except Exception as e:
            logger.error(f"❌ Error calculating technique score: {e}")
            return 50
    
    def _calculate_rhythm_score(self, frames: List[PoseFrame], target_bpm: Optional[int]) -> int:
        """Calculate rhythm score (0-100)"""
        try:
            # Beat synchronization
            beat_sync = self._analyze_beat_synchronization(frames, target_bpm)
            
            # Movement timing
            movement_timing = self._analyze_movement_timing(frames)
            
            # Rhythm consistency
            rhythm_consistency = self._analyze_rhythm_consistency(frames)
            
            # Tempo matching
            tempo_matching = self._analyze_tempo_matching(frames, target_bpm)
            
            # Musicality
            musicality = self._analyze_musicality(frames)
            
            # Calculate overall rhythm score
            rhythm_metrics = [
                beat_sync, movement_timing, rhythm_consistency,
                tempo_matching, musicality
            ]
            
            rhythm_score = int(np.mean(rhythm_metrics) * 100)
            return max(0, min(100, rhythm_score))
            
        except Exception as e:
            logger.error(f"❌ Error calculating rhythm score: {e}")
            return 50
    
    def _calculate_expression_score(self, frames: List[PoseFrame]) -> int:
        """Calculate expression score (0-100)"""
        try:
            # Movement flow
            movement_flow = self._analyze_movement_flow(frames)
            
            # Energy expression
            energy_expression = self._analyze_energy_expression(frames)
            
            # Style authenticity
            style_authenticity = self._analyze_style_authenticity(frames)
            
            # Performance quality
            performance_quality = self._analyze_performance_quality(frames)
            
            # Artistic expression
            artistic_expression = self._analyze_artistic_expression(frames)
            
            # Calculate overall expression score
            expression_metrics = [
                movement_flow, energy_expression, style_authenticity,
                performance_quality, artistic_expression
            ]
            
            expression_score = int(np.mean(expression_metrics) * 100)
            return max(0, min(100, expression_score))
            
        except Exception as e:
            logger.error(f"❌ Error calculating expression score: {e}")
            return 50
    
    def _calculate_difficulty_score(self, frames: List[PoseFrame], challenge_difficulty: str) -> int:
        """Calculate difficulty score (0-100)"""
        try:
            # Movement complexity
            movement_complexity = self._analyze_movement_complexity(frames)
            
            # Physical demand
            physical_demand = self._analyze_physical_demand(frames)
            
            # Skill requirement
            skill_requirement = self._analyze_skill_requirement(frames)
            
            # Coordination difficulty
            coordination_difficulty = self._analyze_coordination_difficulty(frames)
            
            # Calculate overall difficulty score
            difficulty_metrics = [
                movement_complexity, physical_demand,
                skill_requirement, coordination_difficulty
            ]
            
            difficulty_score = int(np.mean(difficulty_metrics) * 100)
            
            # Adjust based on challenge difficulty
            difficulty_multipliers = {
                "beginner": 0.7,
                "intermediate": 1.0,
                "advanced": 1.3
            }
            
            multiplier = difficulty_multipliers.get(challenge_difficulty, 1.0)
            adjusted_difficulty = int(difficulty_score * multiplier)
            
            return max(0, min(100, adjusted_difficulty))
            
        except Exception as e:
            logger.error(f"❌ Error calculating difficulty score: {e}")
            return 50
    
    def _calculate_total_score(self, technique: int, rhythm: int, expression: int, 
                             difficulty: int, challenge_type: str) -> int:
        """Calculate total score with challenge-specific weights"""
        try:
            # Define weights based on challenge type
            weights = {
                "freestyle": {"technique": 0.25, "rhythm": 0.30, "expression": 0.30, "difficulty": 0.15},
                "static": {"technique": 0.40, "rhythm": 0.20, "expression": 0.25, "difficulty": 0.15},
                "spin": {"technique": 0.35, "rhythm": 0.25, "expression": 0.20, "difficulty": 0.20},
                "combo": {"technique": 0.30, "rhythm": 0.25, "expression": 0.25, "difficulty": 0.20}
            }
            
            weight = weights.get(challenge_type, weights["freestyle"])
            
            total_score = (
                technique * weight["technique"] +
                rhythm * weight["rhythm"] +
                expression * weight["expression"] +
                difficulty * weight["difficulty"]
            )
            
            return int(total_score)
            
        except Exception as e:
            logger.error(f"❌ Error calculating total score: {e}")
            return 50
    
    # Enhanced Analysis Methods
    
    def _analyze_balance_stability(self, frames: List[PoseFrame]) -> float:
        """Analyze balance stability"""
        try:
            # Calculate center of mass movement
            com_positions = []
            for frame in frames:
                if frame.keypoints:
                    # Use hip and shoulder points for COM
                    hip_points = [kp for kp in frame.keypoints if "hip" in kp.keypoint_type]
                    shoulder_points = [kp for kp in frame.keypoints if "shoulder" in kp.keypoint_type]
                    
                    if hip_points and shoulder_points:
                        all_points = hip_points + shoulder_points
                        avg_x = sum(kp.x for kp in all_points) / len(all_points)
                        avg_y = sum(kp.y for kp in all_points) / len(all_points)
                        com_positions.append((avg_x, avg_y))
            
            if len(com_positions) < 5:
                return 0.5
            
            # Calculate stability (lower variance = better balance)
            x_positions = [pos[0] for pos in com_positions]
            y_positions = [pos[1] for pos in com_positions]
            
            x_variance = np.var(x_positions)
            y_variance = np.var(y_positions)
            
            # Convert to stability score (0-1)
            stability_score = max(0, 1 - (x_variance + y_variance) * 10)
            return min(1.0, stability_score)
            
        except Exception as e:
            logger.error(f"❌ Error analyzing balance stability: {e}")
            return 0.5
    
    def _analyze_joint_alignment(self, frames: List[PoseFrame]) -> float:
        """Analyze joint alignment"""
        try:
            alignment_scores = []
            for frame in frames:
                if frame.keypoints:
                    # Check shoulder alignment
                    left_shoulder = next((kp for kp in frame.keypoints if kp.keypoint_type == "left_shoulder"), None)
                    right_shoulder = next((kp for kp in frame.keypoints if kp.keypoint_type == "right_shoulder"), None)
                    
                    if left_shoulder and right_shoulder:
                        # Check if shoulders are level
                        shoulder_diff = abs(left_shoulder.y - right_shoulder.y)
                        alignment_score = max(0, 1 - shoulder_diff * 5)
                        alignment_scores.append(alignment_score)
            
            return np.mean(alignment_scores) if alignment_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error analyzing joint alignment: {e}")
            return 0.5
    
    def _analyze_posture_quality(self, frames: List[PoseFrame]) -> float:
        """Analyze posture quality"""
        try:
            posture_scores = []
            for frame in frames:
                if frame.keypoints:
                    # Check spine alignment (shoulder to hip)
                    left_shoulder = next((kp for kp in frame.keypoints if kp.keypoint_type == "left_shoulder"), None)
                    left_hip = next((kp for kp in frame.keypoints if kp.keypoint_type == "left_hip"), None)
                    
                    if left_shoulder and left_hip:
                        # Calculate spine angle
                        spine_angle = abs(left_shoulder.x - left_hip.x)
                        posture_score = max(0, 1 - spine_angle * 2)
                        posture_scores.append(posture_score)
            
            return np.mean(posture_scores) if posture_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error analyzing posture quality: {e}")
            return 0.5
    
    def _analyze_movement_precision(self, frames: List[PoseFrame]) -> float:
        """Analyze movement precision"""
        try:
            precision_scores = []
            for i in range(1, len(frames)):
                if frames[i].keypoints and frames[i-1].keypoints:
                    # Calculate movement smoothness
                    movement_smoothness = self._calculate_movement_smoothness(frames[i-1], frames[i])
                    precision_scores.append(movement_smoothness)
            
            return np.mean(precision_scores) if precision_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error analyzing movement precision: {e}")
            return 0.5
    
    def _analyze_technique_consistency(self, frames: List[PoseFrame]) -> float:
        """Analyze technique consistency"""
        try:
            # Calculate variance in key movements
            movement_variations = []
            for i in range(1, len(frames)):
                if frames[i].keypoints and frames[i-1].keypoints:
                    variation = self._calculate_frame_variation(frames[i-1], frames[i])
                    movement_variations.append(variation)
            
            if not movement_variations:
                return 0.5
            
            # Lower variance = more consistent technique
            consistency_score = max(0, 1 - np.std(movement_variations) * 2)
            return min(1.0, consistency_score)
            
        except Exception as e:
            logger.error(f"❌ Error analyzing technique consistency: {e}")
            return 0.5
    
    # Rhythm Analysis Methods
    
    def _analyze_beat_synchronization(self, frames: List[PoseFrame], target_bpm: Optional[int]) -> float:
        """Analyze beat synchronization"""
        try:
            if not target_bpm or len(frames) < 10:
                return 0.5
            
            # Calculate movement peaks
            movement_magnitudes = []
            for i in range(1, len(frames)):
                if frames[i].keypoints and frames[i-1].keypoints:
                    movement = self._calculate_frame_movement(frames[i-1], frames[i])
                    movement_magnitudes.append(movement)
            
            if len(movement_magnitudes) < 5:
                return 0.5
            
            # Simple rhythm analysis
            avg_movement = np.mean(movement_magnitudes)
            movement_variance = np.var(movement_magnitudes)
            
            rhythm_score = max(0, 1 - movement_variance * 5)
            return min(1.0, rhythm_score)
            
        except Exception as e:
            logger.error(f"❌ Error analyzing beat synchronization: {e}")
            return 0.5
    
    def _analyze_movement_timing(self, frames: List[PoseFrame]) -> float:
        """Analyze movement timing"""
        try:
            timing_scores = []
            for i in range(2, len(frames)):
                if frames[i].keypoints and frames[i-1].keypoints and frames[i-2].keypoints:
                    timing_consistency = self._calculate_timing_consistency(frames[i-2:i+1])
                    timing_scores.append(timing_consistency)
            
            return np.mean(timing_scores) if timing_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error analyzing movement timing: {e}")
            return 0.5
    
    def _analyze_rhythm_consistency(self, frames: List[PoseFrame]) -> float:
        """Analyze rhythm consistency"""
        try:
            movement_patterns = []
            for i in range(1, len(frames)):
                if frames[i].keypoints and frames[i-1].keypoints:
                    movement = self._calculate_frame_movement(frames[i-1], frames[i])
                    movement_patterns.append(movement)
            
            if len(movement_patterns) < 5:
                return 0.5
            
            rhythm_variance = np.var(movement_patterns)
            consistency_score = max(0, 1 - rhythm_variance * 5)
            
            return min(1.0, consistency_score)
            
        except Exception as e:
            logger.error(f"❌ Error analyzing rhythm consistency: {e}")
            return 0.5
    
    def _analyze_tempo_matching(self, frames: List[PoseFrame], target_bpm: Optional[int]) -> float:
        """Analyze tempo matching"""
        try:
            if not target_bpm:
                return 0.5
            
            # Calculate overall movement tempo
            total_time = frames[-1].timestamp - frames[0].timestamp
            if total_time <= 0:
                return 0.5
            
            # Count significant movements
            significant_movements = 0
            for i in range(1, len(frames)):
                if frames[i].keypoints and frames[i-1].keypoints:
                    movement = self._calculate_frame_movement(frames[i-1], frames[i])
                    if movement > np.mean([self._calculate_frame_movement(frames[j-1], frames[j]) 
                                         for j in range(1, len(frames)) if frames[j].keypoints and frames[j-1].keypoints]):
                        significant_movements += 1
            
            # Calculate actual BPM
            actual_bpm = (significant_movements / total_time) * 60
            
            # Compare with target BPM
            tempo_match = 1 - abs(actual_bpm - target_bpm) / target_bpm
            return max(0, min(1.0, tempo_match))
            
        except Exception as e:
            logger.error(f"❌ Error analyzing tempo matching: {e}")
            return 0.5
    
    def _analyze_musicality(self, frames: List[PoseFrame]) -> float:
        """Analyze musicality"""
        try:
            rhythm_consistency = self._analyze_rhythm_consistency(frames)
            movement_flow = self._analyze_movement_flow(frames)
            
            musicality_score = (rhythm_consistency + movement_flow) / 2
            return musicality_score
            
        except Exception as e:
            logger.error(f"❌ Error analyzing musicality: {e}")
            return 0.5
    
    # Expression Analysis Methods
    
    def _analyze_movement_flow(self, frames: List[PoseFrame]) -> float:
        """Analyze movement flow"""
        try:
            flow_scores = []
            for i in range(2, len(frames)):
                if frames[i].keypoints and frames[i-1].keypoints and frames[i-2].keypoints:
                    smoothness = self._calculate_movement_smoothness(frames[i-2], frames[i-1], frames[i])
                    flow_scores.append(smoothness)
            
            return np.mean(flow_scores) if flow_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error analyzing movement flow: {e}")
            return 0.5
    
    def _analyze_energy_expression(self, frames: List[PoseFrame]) -> float:
        """Analyze energy expression"""
        try:
            energy_scores = []
            for frame in frames:
                if frame.keypoints:
                    # Calculate energy based on movement magnitude
                    energy = sum(kp.confidence for kp in frame.keypoints) / len(frame.keypoints)
                    energy_scores.append(energy)
            
            return np.mean(energy_scores) if energy_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error analyzing energy expression: {e}")
            return 0.5
    
    def _analyze_style_authenticity(self, frames: List[PoseFrame]) -> float:
        """Analyze style authenticity"""
        return 0.7  # Placeholder - would need style-specific analysis
    
    def _analyze_performance_quality(self, frames: List[PoseFrame]) -> float:
        """Analyze performance quality"""
        try:
            technique_consistency = self._analyze_technique_consistency(frames)
            movement_flow = self._analyze_movement_flow(frames)
            energy_expression = self._analyze_energy_expression(frames)
            
            performance_score = (technique_consistency + movement_flow + energy_expression) / 3
            return performance_score
            
        except Exception as e:
            logger.error(f"❌ Error analyzing performance quality: {e}")
            return 0.5
    
    def _analyze_artistic_expression(self, frames: List[PoseFrame]) -> float:
        """Analyze artistic expression"""
        try:
            creativity_scores = []
            for i in range(1, len(frames)):
                if frames[i].keypoints and frames[i-1].keypoints:
                    movement_variety = self._calculate_movement_variety(frames[i-1], frames[i])
                    creativity_scores.append(movement_variety)
            
            return np.mean(creativity_scores) if creativity_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error analyzing artistic expression: {e}")
            return 0.5
    
    # Difficulty Analysis Methods
    
    def _analyze_movement_complexity(self, frames: List[PoseFrame]) -> float:
        """Analyze movement complexity"""
        try:
            complexity_scores = []
            for i in range(1, len(frames)):
                if frames[i].keypoints and frames[i-1].keypoints:
                    complexity = self._calculate_frame_complexity(frames[i-1], frames[i])
                    complexity_scores.append(complexity)
            
            return np.mean(complexity_scores) if complexity_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error analyzing movement complexity: {e}")
            return 0.5
    
    def _analyze_physical_demand(self, frames: List[PoseFrame]) -> float:
        """Analyze physical demand"""
        try:
            demand_scores = []
            for frame in frames:
                if frame.keypoints:
                    # Calculate physical demand based on joint positions
                    demand = sum(1 - kp.y for kp in frame.keypoints if kp.confidence > 0.5) / len(frame.keypoints)
                    demand_scores.append(demand)
            
            return np.mean(demand_scores) if demand_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error analyzing physical demand: {e}")
            return 0.5
    
    def _analyze_skill_requirement(self, frames: List[PoseFrame]) -> float:
        """Analyze skill requirement"""
        try:
            skill_scores = []
            for frame in frames:
                if frame.keypoints:
                    # Calculate skill requirement based on pose complexity
                    skill = sum(abs(kp.x - 0.5) + abs(kp.y - 0.5) for kp in frame.keypoints if kp.confidence > 0.5) / len(frame.keypoints)
                    skill_scores.append(skill)
            
            return np.mean(skill_scores) if skill_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error analyzing skill requirement: {e}")
            return 0.5
    
    def _analyze_coordination_difficulty(self, frames: List[PoseFrame]) -> float:
        """Analyze coordination difficulty"""
        try:
            coordination_scores = []
            for i in range(1, len(frames)):
                if frames[i].keypoints and frames[i-1].keypoints:
                    coordination = self._calculate_frame_complexity(frames[i-1], frames[i])
                    coordination_scores.append(coordination)
            
            return np.mean(coordination_scores) if coordination_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error analyzing coordination difficulty: {e}")
            return 0.5
    
    # Helper Methods
    
    def _calculate_frame_movement(self, frame1: PoseFrame, frame2: PoseFrame) -> float:
        """Calculate movement between two frames"""
        try:
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
            
        except Exception as e:
            logger.error(f"❌ Error calculating frame movement: {e}")
            return 0.0
    
    def _calculate_movement_smoothness(self, frame1: PoseFrame, frame2: PoseFrame, frame3: Optional[PoseFrame] = None) -> float:
        """Calculate movement smoothness"""
        try:
            if frame3 is None:
                # Simple smoothness between two frames
                movement = self._calculate_frame_movement(frame1, frame2)
                return min(1.0, 1 - movement * 2)
            else:
                # Smoothness across three frames
                movement1 = self._calculate_frame_movement(frame1, frame2)
                movement2 = self._calculate_frame_movement(frame2, frame3)
                
                # Smoothness is inversely proportional to acceleration
                acceleration = abs(movement2 - movement1)
                smoothness = max(0, 1.0 - acceleration * 5)
                return min(1.0, smoothness)
                
        except Exception as e:
            logger.error(f"❌ Error calculating movement smoothness: {e}")
            return 0.5
    
    def _calculate_frame_variation(self, frame1: PoseFrame, frame2: PoseFrame) -> float:
        """Calculate variation between frames"""
        try:
            return self._calculate_frame_movement(frame1, frame2)
        except Exception as e:
            logger.error(f"❌ Error calculating frame variation: {e}")
            return 0.0
    
    def _calculate_timing_consistency(self, frames: List[PoseFrame]) -> float:
        """Calculate timing consistency across frames"""
        try:
            if len(frames) < 3:
                return 0.5
            
            movements = []
            for i in range(1, len(frames)):
                if frames[i].keypoints and frames[i-1].keypoints:
                    movement = self._calculate_frame_movement(frames[i-1], frames[i])
                    movements.append(movement)
            
            # Calculate consistency (lower variance = more consistent)
            variance = np.var(movements)
            consistency = max(0, 1 - variance * 10)
            return min(1.0, consistency)
            
        except Exception as e:
            logger.error(f"❌ Error calculating timing consistency: {e}")
            return 0.5
    
    def _calculate_movement_variety(self, frame1: PoseFrame, frame2: PoseFrame) -> float:
        """Calculate movement variety"""
        try:
            movement = self._calculate_frame_movement(frame1, frame2)
            # Higher movement = more variety
            return min(1.0, movement * 5)
        except Exception as e:
            logger.error(f"❌ Error calculating movement variety: {e}")
            return 0.5
    
    def _calculate_frame_complexity(self, frame1: PoseFrame, frame2: PoseFrame) -> float:
        """Calculate frame complexity"""
        try:
            # Analyze which body parts moved
            moved_parts = 0
            total_parts = 0
            
            frame1_map = {kp.keypoint_type: kp for kp in frame1.keypoints}
            frame2_map = {kp.keypoint_type: kp for kp in frame2.keypoints}
            
            for kp_type in frame1_map:
                if kp_type in frame2_map:
                    total_parts += 1
                    kp1 = frame1_map[kp_type]
                    kp2 = frame2_map[kp_type]
                    
                    distance = np.sqrt((kp2.x - kp1.x)**2 + (kp2.y - kp1.y)**2)
                    if distance > 0.01:  # Threshold for movement
                        moved_parts += 1
            
            complexity = moved_parts / total_parts if total_parts > 0 else 0.0
            return complexity
            
        except Exception as e:
            logger.error(f"❌ Error calculating frame complexity: {e}")
            return 0.5
    
    def _calculate_analysis_confidence(self, valid_frames: List[PoseFrame], total_frames: List[PoseFrame]) -> float:
        """Calculate analysis confidence"""
        try:
            # Confidence based on percentage of valid frames
            frame_confidence = len(valid_frames) / len(total_frames) if total_frames else 0.0
            
            # Average confidence of valid frames
            avg_confidence = np.mean([f.frame_confidence for f in valid_frames]) if valid_frames else 0.0
            
            # Combined confidence
            combined_confidence = (frame_confidence + avg_confidence) / 2
            return min(1.0, combined_confidence)
            
        except Exception as e:
            logger.error(f"❌ Error calculating analysis confidence: {e}")
            return 0.5
    
    def _generate_enhanced_feedback(self, scores: Dict, challenge_type: str) -> str:
        """Generate enhanced feedback"""
        try:
            feedback_parts = []
            
            # Technique feedback
            technique_score = scores["technique_score"]
            if technique_score >= 80:
                feedback_parts.append("Excellent technique! Your form and execution are outstanding.")
            elif technique_score >= 60:
                feedback_parts.append("Good technique overall. Focus on refining your form and precision.")
            else:
                feedback_parts.append("Work on improving your technique. Focus on proper form and alignment.")
            
            # Rhythm feedback
            rhythm_score = scores["rhythm_score"]
            if rhythm_score >= 80:
                feedback_parts.append("Perfect rhythm and timing! You're really feeling the music.")
            elif rhythm_score >= 60:
                feedback_parts.append("Good rhythm. Try to sync your movements more closely with the beat.")
            else:
                feedback_parts.append("Focus on improving your rhythm and timing. Practice with the music more.")
            
            # Expression feedback
            expression_score = scores["expression_score"]
            if expression_score >= 80:
                feedback_parts.append("Amazing expression and energy! Your performance is captivating.")
            elif expression_score >= 60:
                feedback_parts.append("Good energy and expression. Let yourself go more and show your personality.")
            else:
                feedback_parts.append("Work on expressing yourself more. Don't be afraid to show your personality and energy.")
            
            # Difficulty feedback
            difficulty_score = scores["difficulty_score"]
            if difficulty_score >= 80:
                feedback_parts.append("Impressive difficulty level! You're pushing your limits.")
            elif difficulty_score >= 60:
                feedback_parts.append("Good challenge level. Consider trying more complex movements.")
            else:
                feedback_parts.append("Try to challenge yourself more with complex movements and combinations.")
            
            # Overall feedback
            total_score = scores["total_score"]
            if total_score >= 85:
                feedback_parts.append("Outstanding performance! You're showing great skill and artistry.")
            elif total_score >= 70:
                feedback_parts.append("Great job! Keep practicing and you'll continue to improve.")
            elif total_score >= 50:
                feedback_parts.append("Good effort! Focus on the areas mentioned above to improve.")
            else:
                feedback_parts.append("Keep practicing! Everyone starts somewhere, and you're on your way to improvement.")
            
            return " ".join(feedback_parts)
            
        except Exception as e:
            logger.error(f"❌ Error generating feedback: {e}")
            return "Great effort! Keep practicing and improving your dance skills."
    
    def _get_default_scores(self) -> Dict:
        """Get default scores"""
        return {
            "technique_score": 50,
            "rhythm_score": 50,
            "expression_score": 50,
            "difficulty_score": 50,
            "total_score": 50,
            "confidence": 0.5,
            "breakdown": {
                "technique": 50,
                "rhythm": 50,
                "expression": 50,
                "difficulty": 50
            }
        }
    
    def _get_fallback_analysis_data(self, submission_id: str, error_message: str) -> AnalysisData:
        """Get fallback analysis data"""
        logger.warning(f"⚠️ Using fallback analysis for submission {submission_id}")
        
        return AnalysisData(
            status="failed",
            score=50,
            breakdown={
                "technique": 50,
                "rhythm": 50,
                "expression": 50,
                "difficulty": 50
            },
            feedback=f"Analysis encountered an issue: {error_message}. Please try again or contact support.",
            pose_data_url=None,
            confidence=0.0
        )

# Global service instance
enhanced_scoring_service = EnhancedDanceScoringService() 