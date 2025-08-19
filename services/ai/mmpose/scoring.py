#!/usr/bin/env python3
"""
Simplified Dance Scoring Engine for MMPose
"""

import numpy as np
import logging
from typing import List, Dict, Optional
from datetime import datetime

from .models import (
    DanceScoringResult,
    DanceTechniqueMetrics,
    RhythmMetrics,
    ExpressionMetrics,
    DifficultyMetrics,
    MMPoseFrame,
    ChallengeAnalysisRequest
)

logger = logging.getLogger(__name__)

class DanceScoringEngine:
    """Simplified dance scoring engine using MMPose data"""
    
    def __init__(self):
        pass
    
    async def calculate_scores(self, pose_frames: List[MMPoseFrame], dance_metrics: Dict, request: ChallengeAnalysisRequest) -> DanceScoringResult:
        """Calculate comprehensive dance scores"""
        try:
            logger.info(f"🎯 Calculating dance scores for {len(pose_frames)} frames")
            
            # Filter frames with good pose detection
            valid_frames = [f for f in pose_frames if f.frame_confidence > 0.5 and len(f.keypoints) >= 10]
            
            if len(valid_frames) < 10:
                logger.warning(f"⚠️ Insufficient valid frames: {len(valid_frames)}")
                return self._get_default_scores(len(pose_frames))
            
            # Calculate technique metrics
            technique_metrics = self._calculate_technique_metrics(valid_frames)
            
            # Calculate rhythm metrics
            rhythm_metrics = self._calculate_rhythm_metrics(valid_frames, request.target_bpm)
            
            # Calculate expression metrics
            expression_metrics = self._calculate_expression_metrics(valid_frames)
            
            # Calculate difficulty metrics
            difficulty_metrics = self._calculate_difficulty_metrics(valid_frames, request.challenge_difficulty)
            
            # Calculate overall scores (0-100)
            technique_score = self._calculate_overall_technique_score(technique_metrics)
            rhythm_score = self._calculate_overall_rhythm_score(rhythm_metrics)
            expression_score = self._calculate_overall_expression_score(expression_metrics)
            difficulty_score = self._calculate_overall_difficulty_score(difficulty_metrics)
            
            # Calculate total score (weighted average)
            total_score = self._calculate_total_score(
                technique_score, rhythm_score, expression_score, difficulty_score,
                request.challenge_type
            )
            
            # Calculate confidence
            confidence = self._calculate_analysis_confidence(valid_frames, pose_frames)
            
            return DanceScoringResult(
                technique=technique_metrics,
                rhythm=rhythm_metrics,
                expression=expression_metrics,
                difficulty=difficulty_metrics,
                technique_score=technique_score,
                rhythm_score=rhythm_score,
                expression_score=expression_score,
                difficulty_score=difficulty_score,
                total_score=total_score,
                confidence=confidence,
                processing_time=0.0,
                frames_analyzed=len(valid_frames),
                total_frames=len(pose_frames)
            )
            
        except Exception as e:
            logger.error(f"❌ Error calculating scores: {e}")
            return self._get_default_scores(len(pose_frames))
    
    def _calculate_technique_metrics(self, frames: List[MMPoseFrame]) -> DanceTechniqueMetrics:
        """Calculate dance technique metrics"""
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
            
            return DanceTechniqueMetrics(
                balance_stability=balance_stability,
                joint_alignment=joint_alignment,
                posture_quality=posture_quality,
                movement_precision=movement_precision,
                technique_consistency=technique_consistency
            )
            
        except Exception as e:
            logger.error(f"❌ Error calculating technique metrics: {e}")
            return DanceTechniqueMetrics(
                balance_stability=0.5,
                joint_alignment=0.5,
                posture_quality=0.5,
                movement_precision=0.5,
                technique_consistency=0.5
            )
    
    def _calculate_rhythm_metrics(self, frames: List[MMPoseFrame], target_bpm: Optional[int]) -> RhythmMetrics:
        """Calculate rhythm and timing metrics"""
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
            
            return RhythmMetrics(
                beat_synchronization=beat_sync,
                movement_timing=movement_timing,
                rhythm_consistency=rhythm_consistency,
                tempo_matching=tempo_matching,
                musicality=musicality
            )
            
        except Exception as e:
            logger.error(f"❌ Error calculating rhythm metrics: {e}")
            return RhythmMetrics(
                beat_synchronization=0.5,
                movement_timing=0.5,
                rhythm_consistency=0.5,
                tempo_matching=0.5,
                musicality=0.5
            )
    
    def _calculate_expression_metrics(self, frames: List[MMPoseFrame]) -> ExpressionMetrics:
        """Calculate movement expression metrics"""
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
            
            return ExpressionMetrics(
                movement_flow=movement_flow,
                energy_expression=energy_expression,
                style_authenticity=style_authenticity,
                performance_quality=performance_quality,
                artistic_expression=artistic_expression
            )
            
        except Exception as e:
            logger.error(f"❌ Error calculating expression metrics: {e}")
            return ExpressionMetrics(
                movement_flow=0.5,
                energy_expression=0.5,
                style_authenticity=0.5,
                performance_quality=0.5,
                artistic_expression=0.5
            )
    
    def _calculate_difficulty_metrics(self, frames: List[MMPoseFrame], challenge_difficulty: str) -> DifficultyMetrics:
        """Calculate movement difficulty metrics"""
        try:
            # Movement complexity
            movement_complexity = self._analyze_movement_complexity(frames)
            
            # Physical demand
            physical_demand = self._analyze_physical_demand(frames)
            
            # Skill requirement
            skill_requirement = self._analyze_skill_requirement(frames)
            
            # Coordination difficulty
            coordination_difficulty = self._analyze_coordination_difficulty(frames)
            
            # Overall difficulty
            overall_difficulty = self._analyze_overall_difficulty(frames, challenge_difficulty)
            
            return DifficultyMetrics(
                movement_complexity=movement_complexity,
                physical_demand=physical_demand,
                skill_requirement=skill_requirement,
                coordination_difficulty=coordination_difficulty,
                overall_difficulty=overall_difficulty
            )
            
        except Exception as e:
            logger.error(f"❌ Error calculating difficulty metrics: {e}")
            return DifficultyMetrics(
                movement_complexity=0.5,
                physical_demand=0.5,
                skill_requirement=0.5,
                coordination_difficulty=0.5,
                overall_difficulty=0.5
            )
    
    # Simplified analysis methods
    def _analyze_balance_stability(self, frames: List[MMPoseFrame]) -> float:
        """Analyze balance stability"""
        try:
            # Calculate center of mass movement
            com_positions = []
            for frame in frames:
                if len(frame.keypoints) >= 17:
                    hip_points = [kp for kp in frame.keypoints if "hip" in kp.keypoint_type]
                    if hip_points:
                        avg_x = sum(kp.x for kp in hip_points) / len(hip_points)
                        avg_y = sum(kp.y for kp in hip_points) / len(hip_points)
                        com_positions.append((avg_x, avg_y))
            
            if len(com_positions) < 5:
                return 0.5
            
            x_positions = [pos[0] for pos in com_positions]
            y_positions = [pos[1] for pos in com_positions]
            
            x_variance = np.var(x_positions)
            y_variance = np.var(y_positions)
            
            stability_score = max(0, 1 - (x_variance + y_variance) * 10)
            return min(1.0, stability_score)
            
        except Exception as e:
            logger.error(f"❌ Error analyzing balance stability: {e}")
            return 0.5
    
    def _analyze_joint_alignment(self, frames: List[MMPoseFrame]) -> float:
        """Analyze joint alignment"""
        try:
            alignment_scores = []
            for frame in frames:
                if len(frame.keypoints) >= 17:
                    left_shoulder = next((kp for kp in frame.keypoints if kp.keypoint_type == "left_shoulder"), None)
                    right_shoulder = next((kp for kp in frame.keypoints if kp.keypoint_type == "right_shoulder"), None)
                    
                    if left_shoulder and right_shoulder:
                        shoulder_diff = abs(left_shoulder.y - right_shoulder.y)
                        alignment_score = max(0, 1 - shoulder_diff * 5)
                        alignment_scores.append(alignment_score)
            
            return np.mean(alignment_scores) if alignment_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error analyzing joint alignment: {e}")
            return 0.5
    
    def _analyze_posture_quality(self, frames: List[MMPoseFrame]) -> float:
        """Analyze posture quality"""
        try:
            posture_scores = []
            for frame in frames:
                if len(frame.keypoints) >= 17:
                    left_shoulder = next((kp for kp in frame.keypoints if kp.keypoint_type == "left_shoulder"), None)
                    left_hip = next((kp for kp in frame.keypoints if kp.keypoint_type == "left_hip"), None)
                    
                    if left_shoulder and left_hip:
                        spine_angle = abs(left_shoulder.x - left_hip.x)
                        posture_score = max(0, 1 - spine_angle * 2)
                        posture_scores.append(posture_score)
            
            return np.mean(posture_scores) if posture_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error analyzing posture quality: {e}")
            return 0.5
    
    def _analyze_movement_precision(self, frames: List[MMPoseFrame]) -> float:
        """Analyze movement precision"""
        try:
            precision_scores = []
            for i in range(1, len(frames)):
                movement_smoothness = self._calculate_movement_smoothness(frames[i-1], frames[i])
                precision_scores.append(movement_smoothness)
            
            return np.mean(precision_scores) if precision_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error analyzing movement precision: {e}")
            return 0.5
    
    def _analyze_technique_consistency(self, frames: List[MMPoseFrame]) -> float:
        """Analyze technique consistency"""
        try:
            movement_variations = []
            for i in range(1, len(frames)):
                variation = self._calculate_frame_variation(frames[i-1], frames[i])
                movement_variations.append(variation)
            
            if not movement_variations:
                return 0.5
            
            consistency_score = max(0, 1 - np.std(movement_variations) * 2)
            return min(1.0, consistency_score)
            
        except Exception as e:
            logger.error(f"❌ Error analyzing technique consistency: {e}")
            return 0.5
    
    # Rhythm analysis methods
    def _analyze_beat_synchronization(self, frames: List[MMPoseFrame], target_bpm: Optional[int]) -> float:
        """Analyze beat synchronization"""
        try:
            if not target_bpm or len(frames) < 10:
                return 0.5
            
            movement_magnitudes = []
            for i in range(1, len(frames)):
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
    
    def _analyze_movement_timing(self, frames: List[MMPoseFrame]) -> float:
        """Analyze movement timing"""
        try:
            timing_scores = []
            for i in range(2, len(frames)):
                timing_consistency = self._calculate_timing_consistency(frames[i-2:i+1])
                timing_scores.append(timing_consistency)
            
            return np.mean(timing_scores) if timing_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error analyzing movement timing: {e}")
            return 0.5
    
    def _analyze_rhythm_consistency(self, frames: List[MMPoseFrame]) -> float:
        """Analyze rhythm consistency"""
        try:
            movement_patterns = []
            for i in range(1, len(frames)):
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
    
    def _analyze_tempo_matching(self, frames: List[MMPoseFrame], target_bpm: Optional[int]) -> float:
        """Analyze tempo matching"""
        try:
            if not target_bpm:
                return 0.5
            
            # Simple tempo analysis
            total_time = frames[-1].timestamp - frames[0].timestamp
            if total_time <= 0:
                return 0.5
            
            significant_movements = 0
            for i in range(1, len(frames)):
                movement = self._calculate_frame_movement(frames[i-1], frames[i])
                if movement > np.mean([self._calculate_frame_movement(frames[j-1], frames[j]) 
                                     for j in range(1, len(frames))]):
                    significant_movements += 1
            
            actual_bpm = (significant_movements / total_time) * 60
            tempo_match = 1 - abs(actual_bpm - target_bpm) / target_bpm
            return max(0, min(1.0, tempo_match))
            
        except Exception as e:
            logger.error(f"❌ Error analyzing tempo matching: {e}")
            return 0.5
    
    def _analyze_musicality(self, frames: List[MMPoseFrame]) -> float:
        """Analyze musicality"""
        try:
            rhythm_consistency = self._analyze_rhythm_consistency(frames)
            movement_flow = self._analyze_movement_flow(frames)
            
            musicality_score = (rhythm_consistency + movement_flow) / 2
            return musicality_score
            
        except Exception as e:
            logger.error(f"❌ Error analyzing musicality: {e}")
            return 0.5
    
    # Expression analysis methods
    def _analyze_movement_flow(self, frames: List[MMPoseFrame]) -> float:
        """Analyze movement flow"""
        try:
            flow_scores = []
            for i in range(2, len(frames)):
                smoothness = self._calculate_movement_smoothness(frames[i-2], frames[i-1], frames[i])
                flow_scores.append(smoothness)
            
            return np.mean(flow_scores) if flow_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error analyzing movement flow: {e}")
            return 0.5
    
    def _analyze_energy_expression(self, frames: List[MMPoseFrame]) -> float:
        """Analyze energy expression"""
        try:
            energy_scores = []
            for frame in frames:
                if len(frame.keypoints) >= 10:
                    energy = sum(kp.confidence for kp in frame.keypoints) / len(frame.keypoints)
                    energy_scores.append(energy)
            
            return np.mean(energy_scores) if energy_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error analyzing energy expression: {e}")
            return 0.5
    
    def _analyze_style_authenticity(self, frames: List[MMPoseFrame]) -> float:
        """Analyze style authenticity"""
        return 0.7  # Placeholder
    
    def _analyze_performance_quality(self, frames: List[MMPoseFrame]) -> float:
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
    
    def _analyze_artistic_expression(self, frames: List[MMPoseFrame]) -> float:
        """Analyze artistic expression"""
        try:
            creativity_scores = []
            for i in range(1, len(frames)):
                movement_variety = self._calculate_movement_variety(frames[i-1], frames[i])
                creativity_scores.append(movement_variety)
            
            return np.mean(creativity_scores) if creativity_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error analyzing artistic expression: {e}")
            return 0.5
    
    # Difficulty analysis methods
    def _analyze_movement_complexity(self, frames: List[MMPoseFrame]) -> float:
        """Analyze movement complexity"""
        try:
            complexity_scores = []
            for i in range(1, len(frames)):
                complexity = self._calculate_frame_complexity(frames[i-1], frames[i])
                complexity_scores.append(complexity)
            
            return np.mean(complexity_scores) if complexity_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error analyzing movement complexity: {e}")
            return 0.5
    
    def _analyze_physical_demand(self, frames: List[MMPoseFrame]) -> float:
        """Analyze physical demand"""
        try:
            demand_scores = []
            for frame in frames:
                if len(frame.keypoints) >= 10:
                    demand = self._calculate_physical_demand(frame)
                    demand_scores.append(demand)
            
            return np.mean(demand_scores) if demand_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error analyzing physical demand: {e}")
            return 0.5
    
    def _analyze_skill_requirement(self, frames: List[MMPoseFrame]) -> float:
        """Analyze skill requirement"""
        try:
            skill_scores = []
            for frame in frames:
                if len(frame.keypoints) >= 10:
                    skill = self._calculate_skill_requirement(frame)
                    skill_scores.append(skill)
            
            return np.mean(skill_scores) if skill_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error analyzing skill requirement: {e}")
            return 0.5
    
    def _analyze_coordination_difficulty(self, frames: List[MMPoseFrame]) -> float:
        """Analyze coordination difficulty"""
        try:
            coordination_scores = []
            for i in range(1, len(frames)):
                coordination = self._calculate_coordination_difficulty(frames[i-1], frames[i])
                coordination_scores.append(coordination)
            
            return np.mean(coordination_scores) if coordination_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error analyzing coordination difficulty: {e}")
            return 0.5
    
    def _analyze_overall_difficulty(self, frames: List[MMPoseFrame], challenge_difficulty: str) -> float:
        """Analyze overall difficulty"""
        try:
            complexity = self._analyze_movement_complexity(frames)
            demand = self._analyze_physical_demand(frames)
            skill = self._analyze_skill_requirement(frames)
            coordination = self._analyze_coordination_difficulty(frames)
            
            overall_difficulty = (complexity + demand + skill + coordination) / 4
            
            difficulty_multipliers = {
                "beginner": 0.7,
                "intermediate": 1.0,
                "advanced": 1.3
            }
            
            multiplier = difficulty_multipliers.get(challenge_difficulty, 1.0)
            adjusted_difficulty = overall_difficulty * multiplier
            
            return min(1.0, adjusted_difficulty)
            
        except Exception as e:
            logger.error(f"❌ Error analyzing overall difficulty: {e}")
            return 0.5
    
    # Score calculation methods
    def _calculate_overall_technique_score(self, technique: DanceTechniqueMetrics) -> int:
        """Calculate overall technique score (0-100)"""
        try:
            scores = [
                technique.balance_stability,
                technique.joint_alignment,
                technique.posture_quality,
                technique.movement_precision,
                technique.technique_consistency
            ]
            return int(np.mean(scores) * 100)
        except Exception as e:
            logger.error(f"❌ Error calculating technique score: {e}")
            return 50
    
    def _calculate_overall_rhythm_score(self, rhythm: RhythmMetrics) -> int:
        """Calculate overall rhythm score (0-100)"""
        try:
            scores = [
                rhythm.beat_synchronization,
                rhythm.movement_timing,
                rhythm.rhythm_consistency,
                rhythm.tempo_matching,
                rhythm.musicality
            ]
            return int(np.mean(scores) * 100)
        except Exception as e:
            logger.error(f"❌ Error calculating rhythm score: {e}")
            return 50
    
    def _calculate_overall_expression_score(self, expression: ExpressionMetrics) -> int:
        """Calculate overall expression score (0-100)"""
        try:
            scores = [
                expression.movement_flow,
                expression.energy_expression,
                expression.style_authenticity,
                expression.performance_quality,
                expression.artistic_expression
            ]
            return int(np.mean(scores) * 100)
        except Exception as e:
            logger.error(f"❌ Error calculating expression score: {e}")
            return 50
    
    def _calculate_overall_difficulty_score(self, difficulty: DifficultyMetrics) -> int:
        """Calculate overall difficulty score (0-100)"""
        try:
            scores = [
                difficulty.movement_complexity,
                difficulty.physical_demand,
                difficulty.skill_requirement,
                difficulty.coordination_difficulty,
                difficulty.overall_difficulty
            ]
            return int(np.mean(scores) * 100)
        except Exception as e:
            logger.error(f"❌ Error calculating difficulty score: {e}")
            return 50
    
    def _calculate_total_score(self, technique: int, rhythm: int, expression: int, difficulty: int, challenge_type: str) -> int:
        """Calculate total score with challenge-specific weights"""
        try:
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
    
    def _calculate_analysis_confidence(self, valid_frames: List[MMPoseFrame], total_frames: List[MMPoseFrame]) -> float:
        """Calculate analysis confidence"""
        try:
            frame_confidence = len(valid_frames) / len(total_frames) if total_frames else 0.0
            avg_confidence = np.mean([f.frame_confidence for f in valid_frames]) if valid_frames else 0.0
            
            combined_confidence = (frame_confidence + avg_confidence) / 2
            return min(1.0, combined_confidence)
            
        except Exception as e:
            logger.error(f"❌ Error calculating analysis confidence: {e}")
            return 0.5
    
    # Helper methods
    def _calculate_frame_movement(self, frame1: MMPoseFrame, frame2: MMPoseFrame) -> float:
        """Calculate movement between two frames"""
        try:
            if not frame1.keypoints or not frame2.keypoints:
                return 0.0
            
            total_movement = 0.0
            valid_pairs = 0
            
            frame1_map = {kp.keypoint_type: kp for kp in frame1.keypoints}
            frame2_map = {kp.keypoint_type: kp for kp in frame2.keypoints}
            
            for kp_type in frame1_map:
                if kp_type in frame2_map:
                    kp1 = frame1_map[kp_type]
                    kp2 = frame2_map[kp_type]
                    
                    distance = np.sqrt((kp2.x - kp1.x)**2 + (kp2.y - kp1.y)**2)
                    total_movement += distance
                    valid_pairs += 1
            
            return total_movement / valid_pairs if valid_pairs > 0 else 0.0
            
        except Exception as e:
            logger.error(f"❌ Error calculating frame movement: {e}")
            return 0.0
    
    def _calculate_movement_smoothness(self, frame1: MMPoseFrame, frame2: MMPoseFrame, frame3: Optional[MMPoseFrame] = None) -> float:
        """Calculate movement smoothness"""
        try:
            if frame3 is None:
                movement = self._calculate_frame_movement(frame1, frame2)
                return min(1.0, 1 - movement * 2)
            else:
                movement1 = self._calculate_frame_movement(frame1, frame2)
                movement2 = self._calculate_frame_movement(frame2, frame3)
                
                acceleration = abs(movement2 - movement1)
                smoothness = max(0, 1.0 - acceleration * 5)
                return min(1.0, smoothness)
                
        except Exception as e:
            logger.error(f"❌ Error calculating movement smoothness: {e}")
            return 0.5
    
    def _calculate_frame_variation(self, frame1: MMPoseFrame, frame2: MMPoseFrame) -> float:
        """Calculate variation between frames"""
        try:
            return self._calculate_frame_movement(frame1, frame2)
        except Exception as e:
            logger.error(f"❌ Error calculating frame variation: {e}")
            return 0.0
    
    def _calculate_timing_consistency(self, frames: List[MMPoseFrame]) -> float:
        """Calculate timing consistency"""
        try:
            if len(frames) < 3:
                return 0.5
            
            movements = []
            for i in range(1, len(frames)):
                movement = self._calculate_frame_movement(frames[i-1], frames[i])
                movements.append(movement)
            
            variance = np.var(movements)
            consistency = max(0, 1 - variance * 10)
            return min(1.0, consistency)
            
        except Exception as e:
            logger.error(f"❌ Error calculating timing consistency: {e}")
            return 0.5
    
    def _calculate_movement_variety(self, frame1: MMPoseFrame, frame2: MMPoseFrame) -> float:
        """Calculate movement variety"""
        try:
            movement = self._calculate_frame_movement(frame1, frame2)
            return min(1.0, movement * 5)
        except Exception as e:
            logger.error(f"❌ Error calculating movement variety: {e}")
            return 0.5
    
    def _calculate_frame_complexity(self, frame1: MMPoseFrame, frame2: MMPoseFrame) -> float:
        """Calculate frame complexity"""
        try:
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
                    if distance > 0.01:
                        moved_parts += 1
            
            complexity = moved_parts / total_parts if total_parts > 0 else 0.0
            return complexity
            
        except Exception as e:
            logger.error(f"❌ Error calculating frame complexity: {e}")
            return 0.5
    
    def _calculate_physical_demand(self, frame: MMPoseFrame) -> float:
        """Calculate physical demand"""
        try:
            demand_score = 0.0
            valid_joints = 0
            
            for kp in frame.keypoints:
                if kp.confidence > 0.5:
                    demand_score += (1 - kp.y)
                    valid_joints += 1
            
            return demand_score / valid_joints if valid_joints > 0 else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error calculating physical demand: {e}")
            return 0.5
    
    def _calculate_skill_requirement(self, frame: MMPoseFrame) -> float:
        """Calculate skill requirement"""
        try:
            skill_score = 0.0
            valid_joints = 0
            
            for kp in frame.keypoints:
                if kp.confidence > 0.5:
                    distance_from_center = abs(kp.x - 0.5) + abs(kp.y - 0.5)
                    skill_score += distance_from_center
                    valid_joints += 1
            
            return skill_score / valid_joints if valid_joints > 0 else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error calculating skill requirement: {e}")
            return 0.5
    
    def _calculate_coordination_difficulty(self, frame1: MMPoseFrame, frame2: MMPoseFrame) -> float:
        """Calculate coordination difficulty"""
        try:
            return self._calculate_frame_complexity(frame1, frame2)
        except Exception as e:
            logger.error(f"❌ Error calculating coordination difficulty: {e}")
            return 0.5
    
    def _get_default_scores(self, total_frames: int) -> DanceScoringResult:
        """Get default scores when analysis fails"""
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
            frames_analyzed=0,
            total_frames=total_frames
        ) 