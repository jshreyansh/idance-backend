#!/usr/bin/env python3
"""
Dance Metrics Analyzer for MMPose
"""

import numpy as np
import logging
from typing import List, Dict, Optional
from datetime import datetime

from .models import MMPoseFrame, ChallengeAnalysisRequest

logger = logging.getLogger(__name__)

class DanceMetricsAnalyzer:
    """Analyzer for dance-specific metrics"""
    
    def __init__(self):
        self.dance_styles = {
            "hip_hop": {
                "indicators": ["bounce", "isolations", "groove"],
                "key_movements": ["popping", "locking", "breaking"]
            },
            "ballet": {
                "indicators": ["turnout", "extension", "grace"],
                "key_movements": ["plie", "tendu", "pirouette"]
            },
            "contemporary": {
                "indicators": ["flow", "release", "weight"],
                "key_movements": ["fall", "roll", "spiral"]
            },
            "jazz": {
                "indicators": ["energy", "sharpness", "style"],
                "key_movements": ["kick", "leap", "turn"]
            }
        }
    
    async def analyze_dance_metrics(self, pose_frames: List[MMPoseFrame], request: ChallengeAnalysisRequest) -> Dict:
        """Analyze dance-specific metrics"""
        try:
            logger.info(f"🎭 Analyzing dance metrics for {len(pose_frames)} frames")
            
            metrics = {
                "movement_analysis": self._analyze_movement_patterns(pose_frames),
                "style_detection": self._detect_dance_style(pose_frames),
                "skill_assessment": self._assess_skill_level(pose_frames, request.challenge_difficulty),
                "performance_metrics": self._calculate_performance_metrics(pose_frames),
                "technical_analysis": self._analyze_technical_elements(pose_frames)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Error analyzing dance metrics: {e}")
            return {}
    
    def _analyze_movement_patterns(self, frames: List[MMPoseFrame]) -> Dict:
        """Analyze movement patterns"""
        try:
            if len(frames) < 5:
                return {"error": "Insufficient frames for analysis"}
            
            # Analyze movement phases
            movement_phases = self._identify_movement_phases(frames)
            
            # Analyze key transitions
            key_transitions = self._identify_key_transitions(frames)
            
            # Analyze movement patterns
            movement_patterns = self._identify_movement_patterns(frames)
            
            # Analyze energy distribution
            energy_distribution = self._analyze_energy_distribution(frames)
            
            # Analyze spatial usage
            spatial_usage = self._analyze_spatial_usage(frames)
            
            return {
                "movement_phases": movement_phases,
                "key_transitions": key_transitions,
                "movement_patterns": movement_patterns,
                "energy_distribution": energy_distribution,
                "spatial_usage": spatial_usage
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing movement patterns: {e}")
            return {}
    
    def _detect_dance_style(self, frames: List[MMPoseFrame]) -> Dict:
        """Detect dance style based on movement patterns"""
        try:
            if len(frames) < 10:
                return {"primary_style": "unknown", "confidence": 0.0}
            
            # Calculate style indicators
            style_scores = {}
            
            for style, config in self.dance_styles.items():
                score = self._calculate_style_score(frames, config["indicators"])
                style_scores[style] = score
            
            # Find primary style
            primary_style = max(style_scores, key=style_scores.get)
            confidence = style_scores[primary_style]
            
            return {
                "primary_style": primary_style,
                "confidence": confidence,
                "style_scores": style_scores
            }
            
        except Exception as e:
            logger.error(f"❌ Error detecting dance style: {e}")
            return {"primary_style": "unknown", "confidence": 0.0}
    
    def _assess_skill_level(self, frames: List[MMPoseFrame], challenge_difficulty: str) -> Dict:
        """Assess skill level based on movement complexity"""
        try:
            # Analyze movement complexity
            complexity = self._analyze_movement_complexity(frames)
            
            # Analyze technique quality
            technique_quality = self._analyze_technique_quality(frames)
            
            # Analyze performance consistency
            consistency = self._analyze_performance_consistency(frames)
            
            # Determine skill level
            skill_level = self._determine_skill_level(complexity, technique_quality, consistency)
            
            return {
                "skill_level": skill_level,
                "complexity_score": complexity,
                "technique_quality": technique_quality,
                "consistency": consistency,
                "challenge_difficulty": challenge_difficulty
            }
            
        except Exception as e:
            logger.error(f"❌ Error assessing skill level: {e}")
            return {"skill_level": "beginner", "complexity_score": 0.5}
    
    def _calculate_performance_metrics(self, frames: List[MMPoseFrame]) -> Dict:
        """Calculate performance metrics"""
        try:
            # Calculate movement efficiency
            efficiency = self._calculate_movement_efficiency(frames)
            
            # Calculate spatial awareness
            spatial_awareness = self._calculate_spatial_awareness(frames)
            
            # Calculate timing accuracy
            timing_accuracy = self._calculate_timing_accuracy(frames)
            
            # Calculate energy management
            energy_management = self._calculate_energy_management(frames)
            
            return {
                "efficiency": efficiency,
                "spatial_awareness": spatial_awareness,
                "timing_accuracy": timing_accuracy,
                "energy_management": energy_management
            }
            
        except Exception as e:
            logger.error(f"❌ Error calculating performance metrics: {e}")
            return {}
    
    def _analyze_technical_elements(self, frames: List[MMPoseFrame]) -> Dict:
        """Analyze technical dance elements"""
        try:
            # Analyze balance
            balance_analysis = self._analyze_balance(frames)
            
            # Analyze coordination
            coordination_analysis = self._analyze_coordination(frames)
            
            # Analyze flexibility
            flexibility_analysis = self._analyze_flexibility(frames)
            
            # Analyze strength
            strength_analysis = self._analyze_strength(frames)
            
            return {
                "balance": balance_analysis,
                "coordination": coordination_analysis,
                "flexibility": flexibility_analysis,
                "strength": strength_analysis
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing technical elements: {e}")
            return {}
    
    # Helper Methods
    
    def _identify_movement_phases(self, frames: List[MMPoseFrame]) -> List[Dict]:
        """Identify different phases of movement"""
        try:
            phases = []
            
            # Simple phase detection based on movement magnitude
            movement_magnitudes = []
            for i in range(1, len(frames)):
                movement = self._calculate_frame_movement(frames[i-1], frames[i])
                movement_magnitudes.append(movement)
            
            # Find peaks and valleys
            peaks, _ = find_peaks(movement_magnitudes, height=np.mean(movement_magnitudes))
            valleys, _ = find_peaks(-np.array(movement_magnitudes), height=-np.mean(movement_magnitudes))
            
            # Create phases
            for i, peak in enumerate(peaks):
                phase = {
                    "type": "peak",
                    "frame": peak,
                    "magnitude": movement_magnitudes[peak],
                    "timestamp": frames[peak].timestamp
                }
                phases.append(phase)
            
            return phases
            
        except Exception as e:
            logger.error(f"❌ Error identifying movement phases: {e}")
            return []
    
    def _identify_key_transitions(self, frames: List[MMPoseFrame]) -> List[Dict]:
        """Identify key movement transitions"""
        try:
            transitions = []
            
            for i in range(2, len(frames)):
                # Calculate transition magnitude
                transition_magnitude = self._calculate_transition_magnitude(frames[i-2:i+1])
                
                if transition_magnitude > np.mean([self._calculate_transition_magnitude(frames[j-2:j+1]) 
                                                for j in range(2, len(frames))]):
                    transition = {
                        "frame": i,
                        "magnitude": transition_magnitude,
                        "timestamp": frames[i].timestamp
                    }
                    transitions.append(transition)
            
            return transitions
            
        except Exception as e:
            logger.error(f"❌ Error identifying key transitions: {e}")
            return []
    
    def _identify_movement_patterns(self, frames: List[MMPoseFrame]) -> List[str]:
        """Identify movement patterns"""
        try:
            patterns = []
            
            # Analyze for common dance patterns
            if self._detect_circular_movement(frames):
                patterns.append("circular_movement")
            
            if self._detect_linear_movement(frames):
                patterns.append("linear_movement")
            
            if self._detect_isolated_movement(frames):
                patterns.append("isolated_movement")
            
            if self._detect_symmetrical_movement(frames):
                patterns.append("symmetrical_movement")
            
            return patterns
            
        except Exception as e:
            logger.error(f"❌ Error identifying movement patterns: {e}")
            return []
    
    def _analyze_energy_distribution(self, frames: List[MMPoseFrame]) -> Dict:
        """Analyze energy distribution throughout the performance"""
        try:
            energy_levels = []
            
            for frame in frames:
                if frame.keypoints:
                    # Calculate energy based on keypoint confidence and positions
                    energy = sum(kp.confidence for kp in frame.keypoints) / len(frame.keypoints)
                    energy_levels.append(energy)
            
            return {
                "mean_energy": np.mean(energy_levels),
                "energy_variance": np.var(energy_levels),
                "peak_energy": np.max(energy_levels),
                "energy_distribution": energy_levels
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing energy distribution: {e}")
            return {}
    
    def _analyze_spatial_usage(self, frames: List[MMPoseFrame]) -> Dict:
        """Analyze spatial usage and movement range"""
        try:
            x_positions = []
            y_positions = []
            
            for frame in frames:
                if frame.keypoints:
                    for kp in frame.keypoints:
                        x_positions.append(kp.x)
                        y_positions.append(kp.y)
            
            return {
                "x_range": (np.min(x_positions), np.max(x_positions)),
                "y_range": (np.min(y_positions), np.max(y_positions)),
                "spatial_coverage": len(set([(round(x, 2), round(y, 2)) for x, y in zip(x_positions, y_positions)]))
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing spatial usage: {e}")
            return {}
    
    def _calculate_style_score(self, frames: List[MMPoseFrame], indicators: List[str]) -> float:
        """Calculate score for a specific dance style"""
        try:
            score = 0.0
            total_indicators = len(indicators)
            
            for indicator in indicators:
                if indicator == "bounce":
                    score += self._calculate_bounce_score(frames)
                elif indicator == "isolations":
                    score += self._calculate_isolation_score(frames)
                elif indicator == "groove":
                    score += self._calculate_groove_score(frames)
                elif indicator == "turnout":
                    score += self._calculate_turnout_score(frames)
                elif indicator == "extension":
                    score += self._calculate_extension_score(frames)
                elif indicator == "grace":
                    score += self._calculate_grace_score(frames)
                elif indicator == "flow":
                    score += self._calculate_flow_score(frames)
                elif indicator == "release":
                    score += self._calculate_release_score(frames)
                elif indicator == "weight":
                    score += self._calculate_weight_score(frames)
                elif indicator == "energy":
                    score += self._calculate_energy_score(frames)
                elif indicator == "sharpness":
                    score += self._calculate_sharpness_score(frames)
                elif indicator == "style":
                    score += self._calculate_style_indicator_score(frames)
            
            return score / total_indicators if total_indicators > 0 else 0.0
            
        except Exception as e:
            logger.error(f"❌ Error calculating style score: {e}")
            return 0.0
    
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
    
    def _analyze_technique_quality(self, frames: List[MMPoseFrame]) -> float:
        """Analyze technique quality"""
        try:
            quality_scores = []
            
            for frame in frames:
                if frame.keypoints:
                    # Analyze joint alignment and posture
                    quality = self._calculate_frame_technique_quality(frame)
                    quality_scores.append(quality)
            
            return np.mean(quality_scores) if quality_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error analyzing technique quality: {e}")
            return 0.5
    
    def _analyze_performance_consistency(self, frames: List[MMPoseFrame]) -> float:
        """Analyze performance consistency"""
        try:
            consistency_scores = []
            
            for i in range(1, len(frames)):
                consistency = self._calculate_frame_consistency(frames[i-1], frames[i])
                consistency_scores.append(consistency)
            
            return np.mean(consistency_scores) if consistency_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ Error analyzing performance consistency: {e}")
            return 0.5
    
    def _determine_skill_level(self, complexity: float, technique: float, consistency: float) -> str:
        """Determine skill level based on metrics"""
        try:
            overall_score = (complexity + technique + consistency) / 3
            
            if overall_score >= 0.8:
                return "advanced"
            elif overall_score >= 0.6:
                return "intermediate"
            else:
                return "beginner"
                
        except Exception as e:
            logger.error(f"❌ Error determining skill level: {e}")
            return "beginner"
    
    # Additional helper methods for style detection
    
    def _calculate_bounce_score(self, frames: List[MMPoseFrame]) -> float:
        """Calculate bounce score for hip-hop detection"""
        try:
            # Analyze vertical movement patterns
            vertical_movements = []
            for i in range(1, len(frames)):
                if frames[i].keypoints and frames[i-1].keypoints:
                    # Calculate vertical movement of hip points
                    hip_movement = self._calculate_vertical_hip_movement(frames[i-1], frames[i])
                    vertical_movements.append(hip_movement)
            
            # Bounce is characterized by regular vertical movement
            if vertical_movements:
                regularity = 1 - np.std(vertical_movements)
                return min(1.0, regularity * 2)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"❌ Error calculating bounce score: {e}")
            return 0.0
    
    def _calculate_isolation_score(self, frames: List[MMPoseFrame]) -> float:
        """Calculate isolation score for hip-hop detection"""
        try:
            isolation_scores = []
            
            for i in range(1, len(frames)):
                isolation = self._calculate_frame_isolation(frames[i-1], frames[i])
                isolation_scores.append(isolation)
            
            return np.mean(isolation_scores) if isolation_scores else 0.0
            
        except Exception as e:
            logger.error(f"❌ Error calculating isolation score: {e}")
            return 0.0
    
    def _calculate_groove_score(self, frames: List[MMPoseFrame]) -> float:
        """Calculate groove score for hip-hop detection"""
        try:
            # Groove is characterized by rhythmic movement patterns
            rhythm_scores = []
            
            for i in range(2, len(frames)):
                rhythm = self._calculate_rhythm_consistency(frames[i-2:i+1])
                rhythm_scores.append(rhythm)
            
            return np.mean(rhythm_scores) if rhythm_scores else 0.0
            
        except Exception as e:
            logger.error(f"❌ Error calculating groove score: {e}")
            return 0.0
    
    # Additional helper methods for movement analysis
    
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
    
    def _calculate_transition_magnitude(self, frames: List[MMPoseFrame]) -> float:
        """Calculate transition magnitude across frames"""
        try:
            if len(frames) < 3:
                return 0.0
            
            movement1 = self._calculate_frame_movement(frames[0], frames[1])
            movement2 = self._calculate_frame_movement(frames[1], frames[2])
            
            # Transition magnitude is the change in movement
            return abs(movement2 - movement1)
            
        except Exception as e:
            logger.error(f"❌ Error calculating transition magnitude: {e}")
            return 0.0
    
    def _detect_circular_movement(self, frames: List[MMPoseFrame]) -> bool:
        """Detect circular movement patterns"""
        try:
            # Simple circular movement detection
            # This is a placeholder - would need more sophisticated analysis
            return False
            
        except Exception as e:
            logger.error(f"❌ Error detecting circular movement: {e}")
            return False
    
    def _detect_linear_movement(self, frames: List[MMPoseFrame]) -> bool:
        """Detect linear movement patterns"""
        try:
            # Simple linear movement detection
            # This is a placeholder - would need more sophisticated analysis
            return False
            
        except Exception as e:
            logger.error(f"❌ Error detecting linear movement: {e}")
            return False
    
    def _detect_isolated_movement(self, frames: List[MMPoseFrame]) -> bool:
        """Detect isolated movement patterns"""
        try:
            # Simple isolated movement detection
            # This is a placeholder - would need more sophisticated analysis
            return False
            
        except Exception as e:
            logger.error(f"❌ Error detecting isolated movement: {e}")
            return False
    
    def _detect_symmetrical_movement(self, frames: List[MMPoseFrame]) -> bool:
        """Detect symmetrical movement patterns"""
        try:
            # Simple symmetrical movement detection
            # This is a placeholder - would need more sophisticated analysis
            return False
            
        except Exception as e:
            logger.error(f"❌ Error detecting symmetrical movement: {e}")
            return False
    
    # Placeholder methods for style indicators
    def _calculate_vertical_hip_movement(self, frame1: MMPoseFrame, frame2: MMPoseFrame) -> float:
        """Calculate vertical hip movement"""
        try:
            # Placeholder implementation
            return 0.0
        except Exception as e:
            logger.error(f"❌ Error calculating vertical hip movement: {e}")
            return 0.0
    
    def _calculate_frame_isolation(self, frame1: MMPoseFrame, frame2: MMPoseFrame) -> float:
        """Calculate frame isolation score"""
        try:
            # Placeholder implementation
            return 0.0
        except Exception as e:
            logger.error(f"❌ Error calculating frame isolation: {e}")
            return 0.0
    
    def _calculate_rhythm_consistency(self, frames: List[MMPoseFrame]) -> float:
        """Calculate rhythm consistency"""
        try:
            # Placeholder implementation
            return 0.0
        except Exception as e:
            logger.error(f"❌ Error calculating rhythm consistency: {e}")
            return 0.0
    
    # Additional placeholder methods for other style indicators
    def _calculate_turnout_score(self, frames: List[MMPoseFrame]) -> float:
        return 0.0
    
    def _calculate_extension_score(self, frames: List[MMPoseFrame]) -> float:
        return 0.0
    
    def _calculate_grace_score(self, frames: List[MMPoseFrame]) -> float:
        return 0.0
    
    def _calculate_flow_score(self, frames: List[MMPoseFrame]) -> float:
        return 0.0
    
    def _calculate_release_score(self, frames: List[MMPoseFrame]) -> float:
        return 0.0
    
    def _calculate_weight_score(self, frames: List[MMPoseFrame]) -> float:
        return 0.0
    
    def _calculate_energy_score(self, frames: List[MMPoseFrame]) -> float:
        return 0.0
    
    def _calculate_sharpness_score(self, frames: List[MMPoseFrame]) -> float:
        return 0.0
    
    def _calculate_style_indicator_score(self, frames: List[MMPoseFrame]) -> float:
        return 0.0
    
    def _calculate_frame_complexity(self, frame1: MMPoseFrame, frame2: MMPoseFrame) -> float:
        return 0.5
    
    def _calculate_frame_technique_quality(self, frame: MMPoseFrame) -> float:
        return 0.5
    
    def _calculate_frame_consistency(self, frame1: MMPoseFrame, frame2: MMPoseFrame) -> float:
        return 0.5
    
    def _calculate_movement_efficiency(self, frames: List[MMPoseFrame]) -> float:
        return 0.5
    
    def _calculate_spatial_awareness(self, frames: List[MMPoseFrame]) -> float:
        return 0.5
    
    def _calculate_timing_accuracy(self, frames: List[MMPoseFrame]) -> float:
        return 0.5
    
    def _calculate_energy_management(self, frames: List[MMPoseFrame]) -> float:
        return 0.5
    
    def _analyze_balance(self, frames: List[MMPoseFrame]) -> Dict:
        return {"score": 0.5}
    
    def _analyze_coordination(self, frames: List[MMPoseFrame]) -> Dict:
        return {"score": 0.5}
    
    def _analyze_flexibility(self, frames: List[MMPoseFrame]) -> Dict:
        return {"score": 0.5}
    
    def _analyze_strength(self, frames: List[MMPoseFrame]) -> Dict:
        return {"score": 0.5} 