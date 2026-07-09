"""
Trajectory Service
==================
Shared service to track vehicle center coordinates over time, calculate motion
vectors, detect flow direction, classify moving states, and assess speed profiles.
Used by Wrong Side, Stop Line Crossing, and Violation modules.
"""
from typing import List, Dict, Tuple, Any, Optional
import numpy as np


class TrajectoryService:
    """
    Tracks trajectory history for ByteTrack vehicle IDs to evaluate motion vectors.
    """

    def __init__(self, max_history_len: int = 30):
        # Maps vehicle_id (int) -> List of Tuple[float, float, float] (x_center, y_center, timestamp)
        self.trajectories: Dict[int, List[Tuple[float, float, float]]] = {}
        self.max_history_len = max_history_len

    def update_trajectory(self, vehicle_id: int, bbox_xyxy: List[float], timestamp: float) -> None:
        """
        Appends the center coordinate of the vehicle's bounding box to its trajectory history.
        """
        if vehicle_id < 0:
            return
            
        x1, y1, x2, y2 = bbox_xyxy
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        
        if vehicle_id not in self.trajectories:
            self.trajectories[vehicle_id] = []
            
        self.trajectories[vehicle_id].append((cx, cy, timestamp))
        
        # Enforce history limit
        if len(self.trajectories[vehicle_id]) > self.max_history_len:
            self.trajectories[vehicle_id].pop(0)

    def get_trajectory(self, vehicle_id: int) -> List[Tuple[float, float, float]]:
        """
        Retrieves the trajectory history list of tuples (cx, cy, timestamp) for a vehicle.
        """
        return self.trajectories.get(vehicle_id, [])

    def get_motion_vector(self, vehicle_id: int) -> Tuple[float, float]:
        """
        Calculates the net displacement vector (dx, dy) over the tracked history.
        Returns (0.0, 0.0) if history is too short (less than 3 points).
        """
        history = self.get_trajectory(vehicle_id)
        if len(history) < 3:
            return (0.0, 0.0)
            
        first_pt = history[0]
        last_pt = history[-1]
        
        dx = last_pt[0] - first_pt[0]
        dy = last_pt[1] - first_pt[1]
        
        return (dx, dy)

    def get_heading_angle(self, vehicle_id: int) -> Optional[float]:
        """
        Calculates heading angle in degrees (0 to 360) relative to positive x-axis.
        """
        dx, dy = self.get_motion_vector(vehicle_id)
        if dx == 0.0 and dy == 0.0:
            return None
        
        angle = np.degrees(np.arctan2(dy, dx))
        if angle < 0:
            angle += 360.0
        return angle

    def get_motion_classification(self, vehicle_id: int, motion_threshold: float = 2.0) -> str:
        """
        Classifies current motion state of the vehicle:
        'moving_forward', 'moving_backward', 'stationary', or 'unknown'.
        """
        history = self.get_trajectory(vehicle_id)
        if len(history) < 3:
            return "unknown"
            
        dx, dy = self.get_motion_vector(vehicle_id)
        displacement = np.sqrt(dx**2 + dy**2)
        
        if displacement < motion_threshold:
            return "stationary"
            
        # Direction analysis (by default y decreases going up, increases going down the screen)
        if dy > 0:
            return "moving_forward"  # Moving down/closer to camera
        else:
            return "moving_backward" # Moving up/away from camera

    def clean_inactive_ids(self, active_ids: List[int]) -> None:
        """
        Removes vehicle trajectories that are no longer active in the current tracking frame.
        """
        inactive = [vid for vid in self.trajectories if vid not in active_ids]
        for vid in inactive:
            self.trajectories.pop(vid, None)

    def reset(self) -> None:
        """Clears all vehicle trajectories."""
        self.trajectories.clear()
