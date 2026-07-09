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

    @staticmethod
    def get_driver_region(vehicle_xyxy: List[float], windshield_height_ratio: float = 0.50, drive_side: str = "RHD") -> List[float]:
        """
        API to get the driver windshield region.
        """
        return DriverRegionService.get_occupant_regions(vehicle_xyxy, windshield_height_ratio, drive_side)["driver"]

    @staticmethod
    def get_passenger_region(vehicle_xyxy: List[float], windshield_height_ratio: float = 0.50, drive_side: str = "RHD") -> List[float]:
        """
        API to get the front passenger windshield region.
        """
        return DriverRegionService.get_occupant_regions(vehicle_xyxy, windshield_height_ratio, drive_side)["passenger"]

    @staticmethod
    def get_head_region(
        vehicle_xyxy: List[float], 
        windshield_height_ratio: float = 0.50, 
        drive_side: str = "RHD", 
        head_height_ratio: float = 0.45
    ) -> List[float]:
        """
        API to get the driver's head region inside the driver windshield box.
        """
        driver_box = DriverRegionService.get_driver_region(vehicle_xyxy, windshield_height_ratio, drive_side)
        dx1, dy1, dx2, dy2 = driver_box
        d_h = dy2 - dy1
        return [dx1, dy1, dx2, dy1 + (d_h * head_height_ratio)]

    @staticmethod
    def get_hand_region(
        vehicle_xyxy: List[float], 
        windshield_height_ratio: float = 0.50, 
        drive_side: str = "RHD", 
        hand_height_ratio: float = 0.40
    ) -> List[float]:
        """
        API to get the driver's hands region (lower part of driver windshield area).
        """
        driver_box = DriverRegionService.get_driver_region(vehicle_xyxy, windshield_height_ratio, drive_side)
        dx1, dy1, dx2, dy2 = driver_box
        d_h = dy2 - dy1
        # Target the lower hand_height_ratio segment of the driver box
        return [dx1, dy2 - (d_h * hand_height_ratio), dx2, dy2]

    @staticmethod
    def get_steering_wheel_region(
        vehicle_xyxy: List[float], 
        windshield_height_ratio: float = 0.50, 
        drive_side: str = "RHD"
    ) -> List[float]:
        """
        API to get steering wheel region (bottom 35% of the driver windshield box).
        """
        return DriverRegionService.get_hand_region(vehicle_xyxy, windshield_height_ratio, drive_side, hand_height_ratio=0.35)

    @staticmethod
    def get_dashboard_region(vehicle_xyxy: List[float], windshield_height_ratio: float = 0.50) -> List[float]:
        """
        API to get the dashboard region (spanning the segment below the windshield, e.g. 50% to 65% of vehicle height).
        """
        vx1, vy1, vx2, vy2 = vehicle_xyxy
        v_h = vy2 - vy1
        dy1 = vy1 + (v_h * windshield_height_ratio)
        dy2 = vy1 + (v_h * (windshield_height_ratio + 0.15))
        return [vx1, dy1, vx2, dy2]


