"""
Road Scene Service
==================
Utility service to centralize road scene geometries: ROIs, stop lines,
intersection boundaries, lane regions, road direction, and perspective helpers.
Shared across Traffic Signal, Wrong Side, Stop Line, and Violation modules.
"""
from typing import List, Dict, Any, Tuple, Optional


class RoadSceneService:
    """
    Central source of truth for road geometry.
    Exposes ROIs scaled to frame dimensions to avoid hardcoded absolute resolutions.
    """

    @staticmethod
    def get_traffic_light_roi(frame_width: int, frame_height: int) -> List[float]:
        """
        Retrieves bounding coordinates [x1, y1, x2, y2] representing the traffic light ROI.
        Typically, traffic signals appear in the upper 40% of the viewport.
        """
        return [0.0, 0.0, float(frame_width), float(frame_height * 0.45)]

    @staticmethod
    def get_intersection_roi(frame_width: int, frame_height: int) -> List[float]:
        """
        Retrieves bounding coordinates representing the intersection area.
        Typically, this covers the middle and lower portion of the viewport.
        """
        return [0.0, float(frame_height * 0.35), float(frame_width), float(frame_height * 0.95)]

    @staticmethod
    def get_stop_line_roi(frame_width: int, frame_height: int) -> List[float]:
        """
        Retrieves bounding coordinates representing the Stop Line zone (placeholder).
        """
        return [float(frame_width * 0.10), float(frame_height * 0.60), float(frame_width * 0.90), float(frame_height * 0.75)]

    @staticmethod
    def get_lane_region(frame_width: int, frame_height: int) -> List[float]:
        """
        Retrieves coordinates representing active lanes (placeholder).
        """
        return [0.0, float(frame_height * 0.50), float(frame_width), float(frame_height * 0.90)]

    @staticmethod
    def get_road_direction(frame_width: int, frame_height: int) -> str:
        """
        Retrieves the main traffic flow direction (placeholder).
        """
        return "incoming"

    @staticmethod
    def get_perspective_matrix(frame_width: int, frame_height: int) -> Optional[Any]:
        """
        Retrieves perspective transformation matrix (placeholder).
        """
        return None

    @staticmethod
    def is_in_roi(box_xyxy: List[float], roi_xyxy: List[float]) -> bool:
        """
        Checks if the center of a bounding box falls within the specified ROI.
        """
        bx1, by1, bx2, by2 = box_xyxy
        rx1, ry1, rx2, ry2 = roi_xyxy
        
        bcx = (bx1 + bx2) / 2
        bcy = (by1 + by2) / 2
        
        return rx1 <= bcx <= rx2 and ry1 <= bcy <= ry2
