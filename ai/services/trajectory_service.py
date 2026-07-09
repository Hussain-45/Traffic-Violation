"""
Trajectory Service
==================
Shared service to track vehicle center coordinates over time, calculate motion
vectors, detect flow direction, classify moving states, and assess speed profiles.
Provides a strongly-typed MotionState model for downstream consumption.
"""
from typing import List, Dict, Tuple, Any, Optional
import numpy as np

from shared.schemas.motion_state import MotionState, Position


class TrajectoryService:
    """
    Tracks trajectory history for ByteTrack vehicle IDs to evaluate motion vectors and MotionState.
    """

    def __init__(self, max_history_len: int = 30):
        # Maps vehicle_id (int) -> List of Tuple[float, float, float] (x_center, y_center, timestamp)
        self.trajectories: Dict[int, List[Tuple[float, float, float]]] = {}
        # Maps vehicle_id (int) -> track age (total updates count)
        self.track_ages: Dict[int, int] = {}
        # Cache for computed MotionState objects per tracking ID
        self.motion_cache: Dict[int, MotionState] = {}
        self.max_history_len = max_history_len

    def update_trajectory(self, vehicle_id: int, bbox_xyxy: List[float], timestamp: float) -> None:
        """
        Appends the center coordinate of the vehicle's bounding box to its trajectory history
        and invalidates/recomputes its MotionState cache.
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

        # Update track age
        self.track_ages[vehicle_id] = self.track_ages.get(vehicle_id, 0) + 1

        # Recompute and cache MotionState immediately (O(1) retrieval)
        self._compute_and_cache_motion_state(vehicle_id, timestamp)

    def get_trajectory(self, vehicle_id: int) -> List[Tuple[float, float, float]]:
        """
        Retrieves the trajectory history list of tuples (cx, cy, timestamp) for a vehicle.
        """
        return self.trajectories.get(vehicle_id, [])

    def get_motion_state(self, vehicle_id: int) -> MotionState:
        """
        Returns the complete strongly-typed MotionState for the given vehicle ID.
        If history is insufficient, returns a valid MotionState with safe defaults.
        """
        # Return cached value if it exists
        if vehicle_id in self.motion_cache:
            return self.motion_cache[vehicle_id]

        # Generate a fallback default MotionState
        history = self.get_trajectory(vehicle_id)
        if history:
            cx, cy, ts = history[-1]
            pos = Position(x=cx, y=cy, timestamp=ts, frame_id=self.track_ages.get(vehicle_id, 1))
        else:
            pos = Position(x=0.0, y=0.0, timestamp=0.0)

        fallback = MotionState(
            tracking_id=vehicle_id,
            current_position=pos,
            timestamp=pos.timestamp,
            history_length=len(history),
            track_age=self.track_ages.get(vehicle_id, 0)
        )
        return fallback

    def _compute_and_cache_motion_state(self, vehicle_id: int, current_ts: float) -> None:
        """
        Performs the complete motion calculations and caches the MotionState.
        """
        history = self.get_trajectory(vehicle_id)
        if not history:
            return

        cx_curr, cy_curr, ts_curr = history[-1]
        frame_idx = self.track_ages.get(vehicle_id, 1)
        curr_pos = Position(x=cx_curr, y=cy_curr, timestamp=ts_curr, frame_id=frame_idx)

        # Base default values
        prev_pos: Optional[Position] = None
        motion_vec = [0.0, 0.0]
        norm_dir = [0.0, 0.0]
        angle: Optional[float] = None
        avg_vel = 0.0
        inst_vel = 0.0
        accel = 0.0
        tot_dist = 0.0
        pred_pos: Optional[Position] = None

        history_len = len(history)

        # 1. Total distance computation
        if history_len > 1:
            for i in range(1, history_len):
                x_prev, y_prev, _ = history[i - 1]
                x_c, y_c, _ = history[i]
                tot_dist += float(np.sqrt((x_c - x_prev)**2 + (y_c - y_prev)**2))

        # 2. Previous position & velocities
        if history_len > 1:
            cx_prev, cy_prev, ts_prev = history[-2]
            prev_pos = Position(x=cx_prev, y=cy_prev, timestamp=ts_prev, frame_id=frame_idx - 1)

            # Motion vector over whole history
            cx_start, cy_start, ts_start = history[0]
            dx = cx_curr - cx_start
            dy = cy_curr - cy_start
            motion_vec = [float(dx), float(dy)]

            # Normalized direction
            magnitude = np.sqrt(dx**2 + dy**2)
            if magnitude > 0:
                norm_dir = [float(dx / magnitude), float(dy / magnitude)]

            # Travel angle
            angle_val = np.degrees(np.arctan2(dy, dx))
            if angle_val < 0:
                angle_val += 360.0
            angle = float(angle_val)

            # Average velocity: total distance over total duration
            total_duration = ts_curr - ts_start
            if total_duration > 0:
                avg_vel = tot_dist / total_duration

            # Instantaneous velocity: distance between last two points over duration
            dt = ts_curr - ts_prev
            if dt > 0:
                step_dist = np.sqrt((cx_curr - cx_prev)**2 + (cy_curr - cy_prev)**2)
                inst_vel = float(step_dist / dt)

                # Linear prediction for next frame (assume dt steps ahead)
                dx_inst = (cx_curr - cx_prev) / dt
                dy_inst = (cy_curr - cy_prev) / dt
                pred_x = cx_curr + dx_inst * dt
                pred_y = cy_curr + dy_inst * dt
                pred_pos = Position(x=float(pred_x), y=float(pred_y), timestamp=ts_curr + dt, frame_id=frame_idx + 1)

        # 3. Acceleration computation (needs last 3 points)
        if history_len > 2:
            cx_p2, cy_p2, ts_p2 = history[-3]
            cx_p1, cy_p1, ts_p1 = history[-2]
            
            dt1 = ts_p1 - ts_p2
            dt2 = ts_curr - ts_p1
            
            if dt1 > 0 and dt2 > 0:
                d1 = np.sqrt((cx_p1 - cx_p2)**2 + (cy_p1 - cy_p2)**2)
                d2 = np.sqrt((cx_curr - cx_p1)**2 + (cy_curr - cy_p1)**2)
                
                v1 = d1 / dt1
                v2 = d2 / dt2
                
                accel = float((v2 - v1) / dt2)

        # Construct strongly-typed MotionState
        state = MotionState(
            tracking_id=vehicle_id,
            current_position=curr_pos,
            previous_position=prev_pos,
            motion_vector=motion_vec,
            normalized_direction=norm_dir,
            travel_angle=angle,
            average_velocity=avg_vel,
            instantaneous_velocity=inst_vel,
            acceleration=accel,
            total_distance=tot_dist,
            history_length=history_len,
            track_age=self.track_ages.get(vehicle_id, 0),
            predicted_position=pred_pos,
            timestamp=current_ts
        )

        self.motion_cache[vehicle_id] = state

    # ── Backward Compatibility Delegations ────────────────────────────────────

    def get_motion_vector(self, vehicle_id: int) -> Tuple[float, float]:
        """Calculates the net displacement vector (dx, dy) over history."""
        state = self.get_motion_state(vehicle_id)
        if len(self.get_trajectory(vehicle_id)) < 3:
            return (0.0, 0.0)
        return (state.motion_vector[0], state.motion_vector[1])

    def get_heading_angle(self, vehicle_id: int) -> Optional[float]:
        """Calculates heading angle in degrees (0 to 360)."""
        state = self.get_motion_state(vehicle_id)
        return state.travel_angle

    def get_motion_classification(self, vehicle_id: int, motion_threshold: float = 2.0) -> str:
        """Classifies current motion state of the vehicle."""
        history = self.get_trajectory(vehicle_id)
        if len(history) < 3:
            return "unknown"
            
        state = self.get_motion_state(vehicle_id)
        displacement = np.sqrt(state.motion_vector[0]**2 + state.motion_vector[1]**2)
        
        if displacement < motion_threshold:
            return "stationary"
            
        # Direction analysis (dy > 0 moving forward, dy <= 0 moving backward)
        if state.motion_vector[1] > 0:
            return "moving_forward"
        else:
            return "moving_backward"

    # ── Cleanup & Lifetime Management ─────────────────────────────────────────

    def clean_inactive_ids(self, active_ids: List[int]) -> None:
        """Removes vehicle trajectories and caches that are no longer active."""
        inactive = [vid for vid in self.trajectories if vid not in active_ids]
        for vid in inactive:
            self.trajectories.pop(vid, None)
            self.track_ages.pop(vid, None)
            self.motion_cache.pop(vid, None)

    def reset(self) -> None:
        """Clears all vehicle trajectories, ages, and caches."""
        self.trajectories.clear()
        self.track_ages.clear()
        self.motion_cache.clear()


# Global singleton instance
trajectory_service = TrajectoryService()

