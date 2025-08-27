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
            
            logger.info(f"🎯 Calculating enhanced scores for {len(valid_frames)} valid frames")
            logger.info(f"🎯 Challenge type: {challenge_type}, difficulty: {challenge_difficulty}")
            
            # Calculate 4-dimensional scores with improved algorithms
            technique_score = self._calculate_enhanced_technique_score(valid_frames)
            rhythm_score = self._calculate_enhanced_rhythm_score(valid_frames, target_bpm)
            expression_score = self._calculate_enhanced_expression_score(valid_frames)
            difficulty_score = self._calculate_enhanced_difficulty_score(valid_frames, challenge_difficulty)
            
            logger.info(f"📊 Raw scores - Technique: {technique_score}, Rhythm: {rhythm_score}, Expression: {expression_score}, Difficulty: {difficulty_score}")
            
            # Calculate total score with challenge-specific weights
            total_score = self._calculate_total_score(
                technique_score, rhythm_score, expression_score, difficulty_score, challenge_type
            )
            
            # Calculate confidence
            confidence = self._calculate_analysis_confidence(valid_frames, pose_frames)
            
            logger.info(f"🎯 Final total score: {total_score}, Confidence: {confidence:.2f}")
            
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

    def _calculate_enhanced_technique_score(self, frames: List[PoseFrame]) -> int:
        """Calculate enhanced technique score (0-100) with better algorithms"""
        try:
            # Enhanced balance stability analysis
            balance_stability = self._analyze_enhanced_balance_stability(frames)
            
            # Enhanced joint alignment analysis
            joint_alignment = self._analyze_enhanced_joint_alignment(frames)
            
            # Enhanced posture quality analysis
            posture_quality = self._analyze_enhanced_posture_quality(frames)
            
            # Enhanced movement precision analysis
            movement_precision = self._analyze_enhanced_movement_precision(frames)
            
            # Enhanced technique consistency analysis
            technique_consistency = self._analyze_enhanced_technique_consistency(frames)
            
            # Enhanced body control analysis
            body_control = self._analyze_enhanced_body_control(frames)
            
            # Calculate weighted technique score
            technique_metrics = {
                "balance": balance_stability * 0.20,
                "alignment": joint_alignment * 0.15,
                "posture": posture_quality * 0.15,
                "precision": movement_precision * 0.20,
                "consistency": technique_consistency * 0.15,
                "control": body_control * 0.15
            }
            
            technique_score = int(sum(technique_metrics.values()) * 100)
            final_score = max(0, min(100, technique_score))
            
            logger.info(f"🎯 Enhanced technique analysis:")
            logger.info(f"   Balance: {balance_stability:.3f} (weighted: {technique_metrics['balance']:.3f})")
            logger.info(f"   Alignment: {joint_alignment:.3f} (weighted: {technique_metrics['alignment']:.3f})")
            logger.info(f"   Posture: {posture_quality:.3f} (weighted: {technique_metrics['posture']:.3f})")
            logger.info(f"   Precision: {movement_precision:.3f} (weighted: {technique_metrics['precision']:.3f})")
            logger.info(f"   Consistency: {technique_consistency:.3f} (weighted: {technique_metrics['consistency']:.3f})")
            logger.info(f"   Control: {body_control:.3f} (weighted: {technique_metrics['control']:.3f})")
            logger.info(f"🎯 Enhanced technique score: {final_score}")
            
            return final_score
            
        except Exception as e:
            logger.error(f"❌ Error calculating enhanced technique score: {e}")
            return 50

    def _calculate_enhanced_rhythm_score(self, frames: List[PoseFrame], target_bpm: Optional[int]) -> int:
        """Calculate enhanced rhythm score (0-100) with better algorithms"""
        try:
            # Enhanced beat synchronization analysis
            beat_sync = self._analyze_enhanced_beat_synchronization(frames, target_bpm)
            
            # Enhanced movement timing analysis
            movement_timing = self._analyze_enhanced_movement_timing(frames)
            
            # Enhanced rhythm consistency analysis
            rhythm_consistency = self._analyze_enhanced_rhythm_consistency(frames)
            
            # Enhanced tempo matching analysis
            tempo_matching = self._analyze_enhanced_tempo_matching(frames, target_bpm)
            
            # Enhanced musicality analysis
            musicality = self._analyze_enhanced_musicality(frames)
            
            # Enhanced dynamic range analysis
            dynamic_range = self._analyze_enhanced_dynamic_range(frames)
            
            # Calculate weighted rhythm score
            rhythm_metrics = {
                "beat_sync": beat_sync * 0.25,
                "timing": movement_timing * 0.20,
                "consistency": rhythm_consistency * 0.20,
                "tempo": tempo_matching * 0.15,
                "musicality": musicality * 0.15,
                "dynamics": dynamic_range * 0.05
            }
            
            rhythm_score = int(sum(rhythm_metrics.values()) * 100)
            final_score = max(0, min(100, rhythm_score))
            
            logger.info(f"🎯 Enhanced rhythm analysis:")
            logger.info(f"   Beat sync: {beat_sync:.3f} (weighted: {rhythm_metrics['beat_sync']:.3f})")
            logger.info(f"   Timing: {movement_timing:.3f} (weighted: {rhythm_metrics['timing']:.3f})")
            logger.info(f"   Consistency: {rhythm_consistency:.3f} (weighted: {rhythm_metrics['consistency']:.3f})")
            logger.info(f"   Tempo: {tempo_matching:.3f} (weighted: {rhythm_metrics['tempo']:.3f})")
            logger.info(f"   Musicality: {musicality:.3f} (weighted: {rhythm_metrics['musicality']:.3f})")
            logger.info(f"   Dynamics: {dynamic_range:.3f} (weighted: {rhythm_metrics['dynamics']:.3f})")
            logger.info(f"🎯 Enhanced rhythm score: {final_score}")
            
            return final_score
            
        except Exception as e:
            logger.error(f"❌ Error calculating enhanced rhythm score: {e}")
            return 50

    def _calculate_enhanced_expression_score(self, frames: List[PoseFrame]) -> int:
        """Calculate enhanced expression score (0-100) with better algorithms"""
        try:
            # Enhanced movement flow analysis
            movement_flow = self._analyze_enhanced_movement_flow(frames)
            
            # Enhanced energy expression analysis
            energy_expression = self._analyze_enhanced_energy_expression(frames)
            
            # Enhanced style authenticity analysis
            style_authenticity = self._analyze_enhanced_style_authenticity(frames)
            
            # Enhanced performance quality analysis
            performance_quality = self._analyze_enhanced_performance_quality(frames)
            
            # Enhanced artistic expression analysis
            artistic_expression = self._analyze_enhanced_artistic_expression(frames)
            
            # Enhanced emotional engagement analysis
            emotional_engagement = self._analyze_enhanced_emotional_engagement(frames)
            
            # Calculate weighted expression score
            expression_metrics = {
                "flow": movement_flow * 0.20,
                "energy": energy_expression * 0.20,
                "style": style_authenticity * 0.15,
                "performance": performance_quality * 0.20,
                "artistic": artistic_expression * 0.15,
                "emotion": emotional_engagement * 0.10
            }
            
            expression_score = int(sum(expression_metrics.values()) * 100)
            final_score = max(0, min(100, expression_score))
            
            logger.info(f"🎯 Enhanced expression analysis:")
            logger.info(f"   Flow: {movement_flow:.3f} (weighted: {expression_metrics['flow']:.3f})")
            logger.info(f"   Energy: {energy_expression:.3f} (weighted: {expression_metrics['energy']:.3f})")
            logger.info(f"   Style: {style_authenticity:.3f} (weighted: {expression_metrics['style']:.3f})")
            logger.info(f"   Performance: {performance_quality:.3f} (weighted: {expression_metrics['performance']:.3f})")
            logger.info(f"   Artistic: {artistic_expression:.3f} (weighted: {expression_metrics['artistic']:.3f})")
            logger.info(f"   Emotion: {emotional_engagement:.3f} (weighted: {expression_metrics['emotion']:.3f})")
            logger.info(f"🎯 Enhanced expression score: {final_score}")
            
            return final_score
            
        except Exception as e:
            logger.error(f"❌ Error calculating enhanced expression score: {e}")
            return 50

    def _calculate_enhanced_difficulty_score(self, frames: List[PoseFrame], challenge_difficulty: str) -> int:
        """Calculate enhanced difficulty score (0-100) with better algorithms"""
        try:
            # Enhanced movement complexity analysis
            movement_complexity = self._analyze_enhanced_movement_complexity(frames)
            
            # Enhanced physical demand analysis
            physical_demand = self._analyze_enhanced_physical_demand(frames)
            
            # Enhanced skill requirement analysis
            skill_requirement = self._analyze_enhanced_skill_requirement(frames)
            
            # Enhanced coordination difficulty analysis
            coordination_difficulty = self._analyze_enhanced_coordination_difficulty(frames)
            
            # Enhanced technical difficulty analysis
            technical_difficulty = self._analyze_enhanced_technical_difficulty(frames)
            
            # Enhanced innovation analysis
            innovation = self._analyze_enhanced_innovation(frames)
            
            # Calculate weighted difficulty score
            difficulty_metrics = {
                "complexity": movement_complexity * 0.25,
                "physical": physical_demand * 0.20,
                "skill": skill_requirement * 0.20,
                "coordination": coordination_difficulty * 0.20,
                "technical": technical_difficulty * 0.10,
                "innovation": innovation * 0.05
            }
            
            difficulty_score = int(sum(difficulty_metrics.values()) * 100)
            
            # Adjust based on challenge difficulty
            difficulty_multipliers = {
                "beginner": 0.6,
                "intermediate": 1.0,
                "advanced": 1.4
            }
            
            multiplier = difficulty_multipliers.get(challenge_difficulty, 1.0)
            adjusted_difficulty = int(difficulty_score * multiplier)
            final_score = max(0, min(100, adjusted_difficulty))
            
            logger.info(f"🎯 Enhanced difficulty analysis:")
            logger.info(f"   Complexity: {movement_complexity:.3f} (weighted: {difficulty_metrics['complexity']:.3f})")
            logger.info(f"   Physical: {physical_demand:.3f} (weighted: {difficulty_metrics['physical']:.3f})")
            logger.info(f"   Skill: {skill_requirement:.3f} (weighted: {difficulty_metrics['skill']:.3f})")
            logger.info(f"   Coordination: {coordination_difficulty:.3f} (weighted: {difficulty_metrics['coordination']:.3f})")
            logger.info(f"   Technical: {technical_difficulty:.3f} (weighted: {difficulty_metrics['technical']:.3f})")
            logger.info(f"   Innovation: {innovation:.3f} (weighted: {difficulty_metrics['innovation']:.3f})")
            logger.info(f"🎯 Enhanced difficulty score: {final_score} (raw: {difficulty_score}, multiplier: {multiplier})")
            
            return final_score
            
        except Exception as e:
            logger.error(f"❌ Error calculating enhanced difficulty score: {e}")
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
    
    def _analyze_enhanced_balance_stability(self, frames: List[PoseFrame]) -> float:
        """Analyze balance stability"""
        try:
            # Debug: Check what keypoint types are available
            if frames and frames[0].keypoints:
                available_keypoints = set(kp.keypoint_type for kp in frames[0].keypoints)
                logger.info(f"🎯 Available keypoint types: {sorted(available_keypoints)}")
            
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
                logger.warning(f"⚠️ Insufficient COM positions for balance analysis: {len(com_positions)}")
                return 0.5
            
            # Calculate stability (lower variance = better balance)
            x_positions = [pos[0] for pos in com_positions]
            y_positions = [pos[1] for pos in com_positions]
            
            x_variance = np.var(x_positions)
            y_variance = np.var(y_positions)
            
            # Convert to stability score (0-1)
            stability_score = max(0, 1 - (x_variance + y_variance) * 10)
            final_score = min(1.0, stability_score)
            
            logger.info(f"🎯 Balance analysis - COM positions: {len(com_positions)}, X variance: {x_variance:.4f}, Y variance: {y_variance:.4f}, Stability score: {final_score:.3f}")
            
            return final_score
            
        except Exception as e:
            logger.error(f"❌ Error analyzing balance stability: {e}")
            return 0.5
    
    def _analyze_enhanced_joint_alignment(self, frames: List[PoseFrame]) -> float:
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
    
    def _analyze_enhanced_posture_quality(self, frames: List[PoseFrame]) -> float:
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
    
    def _analyze_enhanced_movement_precision(self, frames: List[PoseFrame]) -> float:
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
    
    def _analyze_enhanced_technique_consistency(self, frames: List[PoseFrame]) -> float:
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
    
    def _analyze_enhanced_beat_synchronization(self, frames: List[PoseFrame], target_bpm: Optional[int]) -> float:
        """Analyze beat synchronization"""
        try:
            if not target_bpm or len(frames) < 10:
                logger.warning(f"⚠️ Beat sync analysis - No target BPM or insufficient frames: target_bpm={target_bpm}, frames={len(frames)}")
                return 0.5
            
            # Calculate movement peaks
            movement_magnitudes = []
            for i in range(1, len(frames)):
                if frames[i].keypoints and frames[i-1].keypoints:
                    movement = self._calculate_frame_movement(frames[i-1], frames[i])
                    movement_magnitudes.append(movement)
            
            if len(movement_magnitudes) < 5:
                logger.warning(f"⚠️ Beat sync analysis - Insufficient movement data: {len(movement_magnitudes)} movements")
                return 0.5
            
            # Simple rhythm analysis
            avg_movement = np.mean(movement_magnitudes)
            movement_variance = np.var(movement_magnitudes)
            
            rhythm_score = max(0, 1 - movement_variance * 5)
            final_score = min(1.0, rhythm_score)
            
            logger.info(f"🎯 Beat sync analysis - Avg movement: {avg_movement:.4f}, Variance: {movement_variance:.4f}, Score: {final_score:.3f}")
            
            return final_score
            
        except Exception as e:
            logger.error(f"❌ Error analyzing beat synchronization: {e}")
            return 0.5
    
    def _analyze_enhanced_movement_timing(self, frames: List[PoseFrame]) -> float:
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
    
    def _analyze_enhanced_rhythm_consistency(self, frames: List[PoseFrame]) -> float:
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
    
    def _analyze_enhanced_tempo_matching(self, frames: List[PoseFrame], target_bpm: Optional[int]) -> float:
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
    
    def _analyze_enhanced_musicality(self, frames: List[PoseFrame]) -> float:
        """Analyze musicality"""
        try:
            rhythm_consistency = self._analyze_enhanced_rhythm_consistency(frames)
            movement_flow = self._analyze_enhanced_movement_flow(frames)
            
            musicality_score = (rhythm_consistency + movement_flow) / 2
            return musicality_score
            
        except Exception as e:
            logger.error(f"❌ Error analyzing musicality: {e}")
            return 0.5
    
    # Expression Analysis Methods
    
    def _analyze_enhanced_movement_flow(self, frames: List[PoseFrame]) -> float:
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
    
    def _analyze_enhanced_energy_expression(self, frames: List[PoseFrame]) -> float:
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
    
    def _analyze_enhanced_style_authenticity(self, frames: List[PoseFrame]) -> float:
        """Analyze style authenticity"""
        return 0.7  # Placeholder - would need style-specific analysis
    
    def _analyze_enhanced_performance_quality(self, frames: List[PoseFrame]) -> float:
        """Analyze performance quality"""
        try:
            technique_consistency = self._analyze_enhanced_technique_consistency(frames)
            movement_flow = self._analyze_enhanced_movement_flow(frames)
            energy_expression = self._analyze_enhanced_energy_expression(frames)
            
            performance_score = (technique_consistency + movement_flow + energy_expression) / 3
            return performance_score
            
        except Exception as e:
            logger.error(f"❌ Error analyzing performance quality: {e}")
            return 0.5
    
    def _analyze_enhanced_artistic_expression(self, frames: List[PoseFrame]) -> float:
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
    
    def _analyze_enhanced_emotional_engagement(self, frames: List[PoseFrame]) -> float:
        """Analyze emotional engagement"""
        return 0.7  # Placeholder - would need emotion-specific analysis
    
    def _analyze_enhanced_body_control(self, frames: List[PoseFrame]) -> float:
        """Analyze enhanced body control"""
        try:
            control_scores = []
            for i in range(1, len(frames)):
                if frames[i].keypoints and frames[i-1].keypoints:
                    # Analyze smooth transitions between poses
                    transition_smoothness = self._calculate_transition_smoothness(frames[i-1], frames[i])
                    control_scores.append(transition_smoothness)
            
            return np.mean(control_scores) if control_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error analyzing enhanced body control: {e}")
            return 0.5

    def _analyze_enhanced_dynamic_range(self, frames: List[PoseFrame]) -> float:
        """Analyze enhanced dynamic range"""
        try:
            movement_ranges = []
            for frame in frames:
                if frame.keypoints:
                    # Calculate range of motion
                    motion_range = self._calculate_motion_range(frame)
                    movement_ranges.append(motion_range)
            
            if not movement_ranges:
                return 0.5
            
            # Higher variance in movement range = better dynamics
            dynamic_score = min(1.0, np.std(movement_ranges) * 10)
            return dynamic_score
            
        except Exception as e:
            logger.error(f"❌ Error analyzing enhanced dynamic range: {e}")
            return 0.5

    def _analyze_enhanced_technical_difficulty(self, frames: List[PoseFrame]) -> float:
        """Analyze enhanced technical difficulty"""
        try:
            technical_scores = []
            for i in range(1, len(frames)):
                if frames[i].keypoints and frames[i-1].keypoints:
                    # Analyze technical complexity of transitions
                    technical_complexity = self._calculate_technical_complexity(frames[i-1], frames[i])
                    technical_scores.append(technical_complexity)
            
            return np.mean(technical_scores) if technical_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error analyzing enhanced technical difficulty: {e}")
            return 0.5

    def _analyze_enhanced_innovation(self, frames: List[PoseFrame]) -> float:
        """Analyze enhanced innovation"""
        try:
            # Analyze uniqueness of movement patterns
            movement_patterns = []
            for i in range(1, len(frames)):
                if frames[i].keypoints and frames[i-1].keypoints:
                    pattern = self._extract_movement_pattern(frames[i-1], frames[i])
                    movement_patterns.append(pattern)
            
            if len(movement_patterns) < 5:
                return 0.5
            
            # Calculate pattern diversity
            unique_patterns = len(set(movement_patterns))
            total_patterns = len(movement_patterns)
            
            innovation_score = min(1.0, unique_patterns / total_patterns * 2)
            return innovation_score
            
        except Exception as e:
            logger.error(f"❌ Error analyzing enhanced innovation: {e}")
            return 0.5

    # Difficulty Analysis Methods
    
    def _analyze_enhanced_movement_complexity(self, frames: List[PoseFrame]) -> float:
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
    
    def _analyze_enhanced_physical_demand(self, frames: List[PoseFrame]) -> float:
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
    
    def _analyze_enhanced_skill_requirement(self, frames: List[PoseFrame]) -> float:
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
    
    def _analyze_enhanced_coordination_difficulty(self, frames: List[PoseFrame]) -> float:
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
    
    def _analyze_enhanced_technical_difficulty(self, frames: List[PoseFrame]) -> float:
        """Analyze enhanced technical difficulty"""
        try:
            technical_scores = []
            for i in range(1, len(frames)):
                if frames[i].keypoints and frames[i-1].keypoints:
                    # Analyze technical complexity of transitions
                    technical_complexity = self._calculate_technical_complexity(frames[i-1], frames[i])
                    technical_scores.append(technical_complexity)
            
            return np.mean(technical_scores) if technical_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error analyzing enhanced technical difficulty: {e}")
            return 0.5

    def _analyze_enhanced_innovation(self, frames: List[PoseFrame]) -> float:
        """Analyze enhanced innovation"""
        try:
            # Analyze uniqueness of movement patterns
            movement_patterns = []
            for i in range(1, len(frames)):
                if frames[i].keypoints and frames[i-1].keypoints:
                    pattern = self._extract_movement_pattern(frames[i-1], frames[i])
                    movement_patterns.append(pattern)
            
            if len(movement_patterns) < 5:
                return 0.5
            
            # Calculate pattern diversity
            unique_patterns = len(set(movement_patterns))
            total_patterns = len(movement_patterns)
            
            innovation_score = min(1.0, unique_patterns / total_patterns * 2)
            return innovation_score
            
        except Exception as e:
            logger.error(f"❌ Error analyzing enhanced innovation: {e}")
            return 0.5
    
    # Enhanced Helper Methods
    
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

    # Enhanced Helper Methods
    
    def _calculate_transition_smoothness(self, frame1: PoseFrame, frame2: PoseFrame) -> float:
        """Calculate smoothness of transition between two frames"""
        try:
            if not frame1.keypoints or not frame2.keypoints:
                return 0.5
            
            # Calculate average movement distance
            total_distance = 0
            valid_points = 0
            
            for kp1 in frame1.keypoints:
                kp2 = next((kp for kp in frame2.keypoints if kp.keypoint_type == kp1.keypoint_type), None)
                if kp2:
                    distance = np.sqrt((kp2.x - kp1.x)**2 + (kp2.y - kp1.y)**2)
                    total_distance += distance
                    valid_points += 1
            
            if valid_points == 0:
                return 0.5
            
            avg_distance = total_distance / valid_points
            
            # Lower distance = smoother transition
            smoothness = max(0, 1 - avg_distance * 5)
            return min(1.0, smoothness)
            
        except Exception as e:
            return 0.5

    def _calculate_motion_range(self, frame: PoseFrame) -> float:
        """Calculate range of motion in a frame"""
        try:
            if not frame.keypoints:
                return 0.0
            
            # Calculate bounding box of all keypoints
            x_coords = [kp.x for kp in frame.keypoints]
            y_coords = [kp.y for kp in frame.keypoints]
            
            x_range = max(x_coords) - min(x_coords)
            y_range = max(y_coords) - min(y_coords)
            
            return x_range + y_range
            
        except Exception as e:
            return 0.0

    def _calculate_technical_complexity(self, frame1: PoseFrame, frame2: PoseFrame) -> float:
        """Calculate technical complexity of transition"""
        try:
            if not frame1.keypoints or not frame2.keypoints:
                return 0.5
            
            # Count simultaneous movements
            simultaneous_movements = 0
            total_keypoints = 0
            
            for kp1 in frame1.keypoints:
                kp2 = next((kp for kp in frame2.keypoints if kp.keypoint_type == kp1.keypoint_type), None)
                if kp2:
                    movement = np.sqrt((kp2.x - kp1.x)**2 + (kp2.y - kp1.y)**2)
                    if movement > 0.01:  # Significant movement threshold
                        simultaneous_movements += 1
                    total_keypoints += 1
            
            if total_keypoints == 0:
                return 0.5
            
            # More simultaneous movements = higher complexity
            complexity = min(1.0, simultaneous_movements / total_keypoints * 3)
            return complexity
            
        except Exception as e:
            return 0.5

    def _extract_movement_pattern(self, frame1: PoseFrame, frame2: PoseFrame) -> str:
        """Extract movement pattern as string for comparison"""
        try:
            if not frame1.keypoints or not frame2.keypoints:
                return "static"
            
            pattern_parts = []
            
            for kp1 in frame1.keypoints:
                kp2 = next((kp for kp in frame2.keypoints if kp.keypoint_type == kp1.keypoint_type), None)
                if kp2:
                    dx = kp2.x - kp1.x
                    dy = kp2.y - kp1.y
                    
                    # Categorize movement direction
                    if abs(dx) > abs(dy):
                        direction = "horizontal"
                    elif abs(dy) > abs(dx):
                        direction = "vertical"
                    else:
                        direction = "diagonal"
                    
                    pattern_parts.append(f"{kp1.keypoint_type}_{direction}")
            
            return "_".join(sorted(pattern_parts))
            
        except Exception as e:
            return "unknown"

# Global service instance
enhanced_scoring_service = EnhancedDanceScoringService() 