"""
Driver Region Service
=====================
Utility service to centralize calculations for vehicle windshield division,
driver region (e.g. right side for Right-Hand Drive), and passenger region.
Shared across Helmet, Seat Belt, and Mobile Phone detection modules.
"""
from typing import List, Dict, Any, Tuple


class DriverRegionService:
    """
    Centralizes coordinates logic for Windshield, Driver, and Front Passenger regions.
    Supports both Right-Hand Drive (RHD) and Left-Hand Drive (LHD) configurations.
    """

    @staticmethod
    def get_windshield_region(vehicle_xyxy: List[float], windshield_height_ratio: float = 0.50) -> List[float]:
        """
        Extracts the upper windshield bounding box coordinates from a vehicle bbox.
        """
        vx1, vy1, vx2, vy2 = vehicle_xyxy
        v_h = vy2 - vy1
        
        # Windshield spans from top of vehicle down to windshield_height_ratio of its height
        wx1 = vx1
        wy1 = vy1
        wx2 = vx2
        wy2 = vy1 + (v_h * windshield_height_ratio)
        
        return [wx1, wy1, wx2, wy2]

    @staticmethod
    def get_occupant_regions(
        vehicle_xyxy: List[float], 
        windshield_height_ratio: float = 0.50, 
        drive_side: str = "RHD"
    ) -> Dict[str, List[float]]:
        """
        Subdivides the vehicle's windshield region into Driver and Passenger zones.
        
        Parameters:
          vehicle_xyxy: Bounding box coordinates [x1, y1, x2, y2]
          windshield_height_ratio: Ratio of vehicle height representing windshield (0.0 to 1.0)
          drive_side: "RHD" (Right-Hand Drive, e.g. India/UK) or "LHD" (Left-Hand Drive, e.g. US/EU)
          
        Returns:
          Dict containing 'driver' and 'passenger' box coordinates [x1, y1, x2, y2].
        """
        wx1, wy1, wx2, wy2 = DriverRegionService.get_windshield_region(vehicle_xyxy, windshield_height_ratio)
        w_w = wx2 - wx1
        
        left_half = [wx1, wy1, wx1 + w_w * 0.5, wy2]
        right_half = [wx1 + w_w * 0.5, wy1, wx2, wy2]
        
        if drive_side.upper() == "RHD":
            # Driver is on the right, passenger on the left
            return {
                "driver": right_half,
                "passenger": left_half
            }
        else:
            # Driver is on the left, passenger on the right
            return {
                "driver": left_half,
                "passenger": right_half
            }

    @staticmethod
    def get_rider_head_region(rider_xyxy: List[float], head_height_ratio: float = 0.45) -> List[float]:
        """
        Extracts the upper head region box from a rider bounding box.
        """
        rx1, ry1, rx2, ry2 = rider_xyxy
        r_h = ry2 - ry1
        return [rx1, ry1, rx2, ry1 + (r_h * head_height_ratio)]

    @staticmethod
    def get_motorcycle_rider_fallback(motorcycle_xyxy: List[float], height_ratio: float = 0.50) -> List[float]:
        """
        Extracts fallback rider region (upper half of motorcycle box) if no rider is explicitly tracked.
        """
        mx1, my1, mx2, my2 = motorcycle_xyxy
        m_h = my2 - my1
        return [mx1, my1, mx2, my1 + (m_h * height_ratio)]

