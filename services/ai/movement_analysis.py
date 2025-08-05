#!/usr/bin/env python3
"""
Movement Analysis Module for Dance Breakdown
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from scipy.signal import find_peaks
from scipy.stats import pearsonr

logger = logging.getLogger(__name__)

# Joint connections for angle calculations
JOINT_CONNECTIONS = [
    # Upper body
    ("left_shoulder", "left_elbow", "left_wrist"),
    ("right_shoulder", "right_elbow", "right_wrist"),
    ("left_shoulder", "right_shoulder", "right_elbow"),
    ("right_shoulder", "left_shoulder", "left_elbow"),
    # Lower body
    ("left_hip", "left_knee", "left_ankle"),
    ("right_hip", "right_knee", "right_ankle"),
    ("left_hip", "right_hip", "right_knee"),
    ("right_hip", "left_hip", "left_knee"),
    # Core
    ("left_shoulder", "left_hip", "left_knee"),
    ("right_shoulder", "right_hip", "right_knee"),
]

# Joint indices mapping
JOINT_INDICES = {
    "nose": 0, "left_eye_inner": 1, "left_eye": 2, "left_eye_outer": 3,
    "right_eye_inner": 4, "right_eye": 5, "right_eye_outer": 6,
    "left_ear": 7, "right_ear": 8, "mouth_left": 9, "mouth_right": 10,
    "left_shoulder": 11, "right_shoulder": 12, "left_elbow": 13,
    "right_elbow": 14, "left_wrist": 15, "right_wrist": 16,
    "left_pinky": 17, "right_pinky": 18, "left_index": 19,
    "right_index": 20, "left_thumb": 21, "right_thumb": 22,
    "left_hip": 23, "right_hip": 24, "left_knee": 25,
    "right_knee": 26, "left_ankle": 27, "right_ankle": 28,
    "left_heel": 29, "right_heel": 30, "left_foot_index": 31,
    "right_foot_index": 32
}

def calculate_angle(p1: np.ndarray, p2: np.ndarray, p3: np.ndarray) -> float:
    """
    Calculate angle between three points in 3D space
    """
    try:
        # Handle both single points and arrays of points
        if p1.ndim == 1:
            # Single point - calculate single angle
            v1 = p1 - p2
            v2 = p3 - p2
            
            # Normalize vectors
            v1_norm = v1 / np.linalg.norm(v1)
            v2_norm = v2 / np.linalg.norm(v2)
            
            # Calculate angle
            dot_product = np.dot(v1_norm, v2_norm)
            dot_product = np.clip(dot_product, -1.0, 1.0)  # Ensure valid range for arccos
            angle = np.arccos(dot_product)
            
            return np.degrees(angle)
        else:
            # Array of points - calculate angles for each frame
            v1 = p1 - p2
            v2 = p3 - p2
            
            # Normalize vectors
            v1_norm = v1 / np.linalg.norm(v1, axis=1, keepdims=True)
            v2_norm = v2 / np.linalg.norm(v2, axis=1, keepdims=True)
            
            # Calculate angle
            dot_product = np.sum(v1_norm * v2_norm, axis=1)
            dot_product = np.clip(dot_product, -1.0, 1.0)  # Ensure valid range for arccos
            angle = np.arccos(dot_product)
            
            return np.degrees(angle)
    except Exception as e:
        logger.warning(f"Error calculating angle: {str(e)}")
        return 0.0

def calculate_joint_angles(keypoints: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Calculate angles between connected joints
    """
    angles = {}
    
    for start, mid, end in JOINT_CONNECTIONS:
        start_idx = JOINT_INDICES[start]
        mid_idx = JOINT_INDICES[mid]
        end_idx = JOINT_INDICES[end]
        
        angle = calculate_angle(
            keypoints[:, start_idx],
            keypoints[:, mid_idx],
            keypoints[:, end_idx]
        )
        
        angles[f"{start}_{mid}_{end}"] = angle
    
    return angles

def calculate_joint_velocities(keypoints: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Calculate velocities for each joint
    """
    velocities = {}
    for joint_name, idx in JOINT_INDICES.items():
        # Calculate velocity as the difference between consecutive positions
        velocity = np.diff(keypoints[:, idx], axis=0)
        # Calculate magnitude of velocity
        velocity_magnitude = np.linalg.norm(velocity, axis=1)
        velocities[joint_name] = velocity_magnitude
    
    return velocities

def analyze_movement_patterns(keypoints: np.ndarray, joint_angles: Dict[str, np.ndarray]) -> Dict:
    """
    Analyze movement patterns and transitions
    """
    try:
        # Ensure keypoints has the right shape
        if keypoints.ndim != 3:
            logger.warning(f"Expected 3D array, got shape: {keypoints.shape}")
            return {
                "primary_movement": "General movement",
                "rhythm": {"consistency": "moderate"},
                "flow": {"smoothness": "moderate"},
                "transitions": [],
                "symmetry": {"balance": "balanced"},
                "coordination": {"quality": "moderate"}
            }
        
        # Calculate basic movement metrics
        diffs = np.linalg.norm(np.diff(keypoints, axis=0), axis=2)
        total_movement = np.sum(diffs, axis=0)
        
        # Analyze rhythm
        rhythm = analyze_rhythm(total_movement)
        
        # Analyze flow
        flow = analyze_flow(joint_angles)
        
        # Detect transitions
        transitions = detect_transitions(keypoints, joint_angles)
        
        # Analyze symmetry
        symmetry = analyze_symmetry(keypoints)
        
        # Analyze coordination
        coordination = analyze_coordination(keypoints, joint_angles)
        
        return {
            "primary_movement": "General movement",
            "rhythm": rhythm,
            "flow": flow,
            "transitions": transitions,
            "symmetry": symmetry,
            "coordination": coordination
        }
    except Exception as e:
        logger.error(f"Error in movement pattern analysis: {str(e)}")
        return {
            "primary_movement": "General movement",
            "rhythm": {"consistency": "moderate"},
            "flow": {"smoothness": "moderate"},
            "transitions": [],
            "symmetry": {"balance": "balanced"},
            "coordination": {"quality": "moderate"}
        }

def analyze_rhythm(movement: np.ndarray) -> Dict:
    """
    Analyze rhythm of movement
    """
    try:
        # Calculate movement peaks
        peaks, _ = find_peaks(movement, height=np.mean(movement))
        
        # Calculate time between peaks
        peak_intervals = np.diff(peaks)
        
        return {
            "peak_count": len(peaks),
            "average_interval": float(np.mean(peak_intervals)) if len(peak_intervals) > 0 else 0.0,
            "rhythm_consistency": float(np.std(peak_intervals)) if len(peak_intervals) > 0 else 0.0
        }
    except Exception as e:
        logger.warning(f"Error in rhythm analysis: {str(e)}")
        return {
            "peak_count": 0,
            "average_interval": 0.0,
            "rhythm_consistency": 0.0
        }

def analyze_flow(joint_angles: Dict[str, np.ndarray]) -> Dict:
    """
    Analyze flow of movement
    """
    try:
        flow_metrics = {}
        
        for joint_name, angles in joint_angles.items():
            # Calculate smoothness of angle changes
            angle_changes = np.diff(angles)
            flow_metrics[joint_name] = {
                "smoothness": float(np.mean(np.abs(angle_changes))),
                "consistency": float(np.std(angle_changes))
            }
        
        return flow_metrics
    except Exception as e:
        logger.warning(f"Error in flow analysis: {str(e)}")
        return {}

def detect_transitions(keypoints: np.ndarray, joint_angles: Dict[str, np.ndarray]) -> List[Dict]:
    """
    Detect significant movement transitions
    """
    try:
        transitions = []
        
        # Ensure keypoints has the right shape
        if keypoints.ndim != 3:
            logger.warning(f"Expected 3D array for transitions, got shape: {keypoints.shape}")
            return []
        
        # Calculate overall movement magnitude
        movement_magnitude = np.linalg.norm(np.diff(keypoints, axis=0), axis=2)
        total_movement = np.sum(movement_magnitude, axis=1)
        
        # Find significant changes in movement
        threshold = np.mean(total_movement) + np.std(total_movement)
        transition_points = np.where(total_movement > threshold)[0]
        
        for point in transition_points:
            transitions.append({
                "frame": int(point),
                "magnitude": float(total_movement[point]),
                "affected_joints": get_affected_joints(joint_angles, point)
            })
        
        return transitions
    except Exception as e:
        logger.warning(f"Error in transition detection: {str(e)}")
        return []

def get_affected_joints(joint_angles: Dict[str, np.ndarray], frame: int) -> List[str]:
    """
    Get joints that show significant movement at a given frame
    """
    try:
        affected = []
        for joint_name, angles in joint_angles.items():
            if frame < len(angles) - 1:
                angle_change = abs(angles[frame + 1] - angles[frame])
                if angle_change > np.mean(np.abs(np.diff(angles))) + np.std(np.abs(np.diff(angles))):
                    affected.append(joint_name)
        return affected
    except Exception as e:
        logger.warning(f"Error in getting affected joints: {str(e)}")
        return []

def analyze_symmetry(keypoints: np.ndarray) -> Dict:
    """
    Analyze symmetry of movement
    """
    try:
        # Ensure keypoints has the right shape
        if keypoints.ndim != 3:
            logger.warning(f"Expected 3D array for symmetry, got shape: {keypoints.shape}")
            return {
                "overall_symmetry": 0.0,
                "joint_symmetry": {},
                "balance": "balanced"
            }
        
        # Compare left and right side movements
        left_joints = ["left_shoulder", "left_elbow", "left_wrist", "left_hip", "left_knee", "left_ankle"]
        right_joints = ["right_shoulder", "right_elbow", "right_wrist", "right_hip", "right_knee", "right_ankle"]
        
        symmetry_scores = {}
        
        for left, right in zip(left_joints, right_joints):
            left_idx = JOINT_INDICES[left]
            right_idx = JOINT_INDICES[right]
            
            # Calculate movement for each side
            left_movement = np.linalg.norm(np.diff(keypoints[:, left_idx], axis=0), axis=1)
            right_movement = np.linalg.norm(np.diff(keypoints[:, right_idx], axis=0), axis=1)
            
            # Calculate symmetry score
            symmetry_scores[f"{left}_{right}"] = float(np.mean(np.abs(left_movement - right_movement)))
        
        overall_symmetry = float(np.mean(list(symmetry_scores.values()))) if symmetry_scores else 0.0
        
        return {
            "overall_symmetry": overall_symmetry,
            "joint_symmetry": symmetry_scores,
            "balance": "balanced" if overall_symmetry < 0.1 else "unbalanced"
        }
    except Exception as e:
        logger.warning(f"Error in symmetry analysis: {str(e)}")
        return {
            "overall_symmetry": 0.0,
            "joint_symmetry": {},
            "balance": "balanced"
        }

def analyze_coordination(keypoints: np.ndarray, joint_angles: Dict[str, np.ndarray]) -> Dict:
    """
    Analyze coordination between different body parts
    """
    try:
        # Ensure keypoints has the right shape
        if keypoints.ndim != 3:
            logger.warning(f"Expected 3D array for coordination, got shape: {keypoints.shape}")
            return {"upper_lower": 0.0, "quality": "moderate"}
        
        coordination = {}
        
        # Analyze upper-lower body coordination
        upper_body = ["left_shoulder", "right_shoulder", "left_elbow", "right_elbow"]
        lower_body = ["left_hip", "right_hip", "left_knee", "right_knee"]
        
        upper_movement = np.mean([np.linalg.norm(np.diff(keypoints[:, JOINT_INDICES[joint]], axis=0), axis=1) 
                                for joint in upper_body], axis=0)
        lower_movement = np.mean([np.linalg.norm(np.diff(keypoints[:, JOINT_INDICES[joint]], axis=0), axis=1) 
                                for joint in lower_body], axis=0)
        
        # Ensure we have enough data points for correlation
        if len(upper_movement) >= 2 and len(lower_movement) >= 2:
            correlation, _ = pearsonr(upper_movement, lower_movement)
            coordination["upper_lower"] = float(correlation)
        else:
            coordination["upper_lower"] = 0.0
            logger.warning("Insufficient data points for coordination analysis")
        
        coordination["quality"] = "good" if coordination.get("upper_lower", 0) > 0.5 else "moderate"
        
        return coordination
    except Exception as e:
        logger.warning(f"Error in coordination analysis: {str(e)}")
        return {"upper_lower": 0.0, "quality": "moderate"}

def calculate_quality_metrics(keypoints: np.ndarray, joint_angles: Dict[str, np.ndarray], 
                            velocities: Dict[str, np.ndarray]) -> Dict:
    """
    Calculate movement quality metrics
    """
    return {
        "smoothness": calculate_smoothness(velocities),
        "stability": calculate_stability(keypoints),
        "precision": calculate_precision(joint_angles),
        "energy": calculate_energy(velocities),
        "balance": calculate_balance(keypoints)
    }

def calculate_smoothness(velocities: Dict[str, np.ndarray]) -> float:
    """
    Calculate movement smoothness
    """
    # Calculate jerk (rate of change of acceleration)
    jerk_scores = []
    for joint_velocity in velocities.values():
        acceleration = np.diff(joint_velocity)
        jerk = np.diff(acceleration)
        jerk_scores.append(np.mean(np.abs(jerk)))
    
    return float(np.mean(jerk_scores))

def calculate_stability(keypoints: np.ndarray) -> float:
    """
    Calculate movement stability
    """
    # Calculate center of mass movement
    com = np.mean(keypoints, axis=1)
    com_movement = np.linalg.norm(np.diff(com, axis=0), axis=1)
    
    return float(np.mean(com_movement))

def calculate_precision(joint_angles: Dict[str, np.ndarray]) -> float:
    """
    Calculate movement precision
    """
    # Calculate variance in joint angles
    angle_variances = [np.var(angles) for angles in joint_angles.values()]
    
    return float(np.mean(angle_variances))

def calculate_energy(velocities: Dict[str, np.ndarray]) -> float:
    """
    Calculate movement energy
    """
    # Calculate total kinetic energy
    energy = np.mean([np.mean(vel**2) for vel in velocities.values()])
    
    return float(energy)

def calculate_balance(keypoints: np.ndarray) -> float:
    """
    Calculate movement balance
    """
    # Calculate center of mass position relative to support base
    com = np.mean(keypoints, axis=1)
    support_base = np.mean(keypoints[:, [JOINT_INDICES["left_ankle"], JOINT_INDICES["right_ankle"]]], axis=1)
    
    # Calculate distance from COM to support base
    balance = np.linalg.norm(com - support_base, axis=1)
    
    return float(np.mean(balance))

def analyze_movement_enhanced(pose_keypoints: List[Dict], segment: Dict) -> Dict:
    """
    Enhanced movement analysis with detailed metrics
    """
    try:
        # Handle both time-based and index-based segments
        if "start_idx" in segment and "end_idx" in segment:
            start = segment["start_idx"]
            end = segment["end_idx"]
        elif "start_time" in segment and "end_time" in segment:
            # Convert time to frame indices (assuming 15fps)
            fps = 15
            start = int(segment["start_time"] * fps)
            end = int(segment["end_time"] * fps)
        else:
            # Default to first few frames if no timing info
            start = 0
            end = min(10, len(pose_keypoints) - 1)
        
        # Ensure indices are within bounds
        start = max(0, min(start, len(pose_keypoints) - 1))
        end = max(start, min(end, len(pose_keypoints) - 1))
        
        segment_kps = [d["keypoints"] for d in pose_keypoints[start:end+1] if d.get("keypoints") is not None]
        
        if not segment_kps:
            return {"summary": "No pose data for this segment."}
        
        arr = np.stack(segment_kps)
        
        # Calculate all metrics
        joint_angles = calculate_joint_angles(arr)
        joint_velocities = calculate_joint_velocities(arr)
        movement_patterns = analyze_movement_patterns(arr, joint_angles)
        quality_metrics = calculate_quality_metrics(arr, joint_angles, joint_velocities)
        
        return {
            "basic_movement": {
                "top_joints": get_top_moving_joints(arr),
                "main_direction": calculate_main_direction(arr),
                "movement_magnitude": float(np.sum(np.linalg.norm(np.diff(arr, axis=0), axis=2)))
            },
            "joint_analysis": {
                "angles": {k: v.tolist() for k, v in joint_angles.items()},
                "velocities": {k: v.tolist() for k, v in joint_velocities.items()}
            },
            "movement_patterns": movement_patterns,
            "quality_metrics": quality_metrics
        }
        
    except Exception as e:
        logger.error(f"Error in enhanced movement analysis: {str(e)}")
        return {"error": str(e)}

def get_top_moving_joints(keypoints: np.ndarray) -> List[str]:
    """
    Get top moving joints
    """
    diffs = np.linalg.norm(np.diff(keypoints, axis=0), axis=2)
    total_movement = np.sum(diffs, axis=0)
    top_indices = np.argsort(total_movement)[-5:][::-1]
    
    return [list(JOINT_INDICES.keys())[i] for i in top_indices]

def calculate_main_direction(keypoints: np.ndarray) -> str:
    """
    Calculate main direction of movement
    """
    mean_diff = np.mean(np.diff(keypoints, axis=0), axis=(0, 1))
    if mean_diff[0] < -0.01:
        return "left"
    elif mean_diff[0] > 0.01:
        return "right"
    else:
        return "center" 