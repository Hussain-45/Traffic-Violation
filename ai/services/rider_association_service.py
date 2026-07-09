"""
Rider Association Service
==========================
Associates tracked riders (persons) with their corresponding motorcycles using
spatial overlap (IoU), center distance, relative sorting, and temporal heading flow.
Serves as the single source of truth for occupant positioning index.
"""
import os
import yaml
import numpy as np
from typing import List, Dict, Tuple, Any, Optional
from loguru import logger

from shared.schemas.rider_group import RiderInfo, MotorcycleGroup
from ai.services.trajectory_service import trajectory_service


class RiderAssociationService:
    """
    Manages spatial and relative rider-to-motorcycle group associations.
    """

    def __init__(self, pipeline_config_path: str = "configs/pipeline.yaml"):
        self.pipeline_config_path = pipeline_config_path
        self.config: Dict[str, Any] = {}
        # Cached motorcycle groups: motorcycle_tracking_id -> MotorcycleGroup
        self.motorcycle_groups: Dict[int, MotorcycleGroup] = {}
        self.load_config()

    def load_config(self) -> None:
        """Loads parameters from pipeline.yaml, falling back to safe defaults."""
        if os.path.exists(self.pipeline_config_path):
            try:
                with open(self.pipeline_config_path, "r") as f:
                    full_cfg = yaml.safe_load(f) or {}
                # Look under modules -> triple_riding_detection or create a rider_association key
                modules = full_cfg.get("modules", {})
                self.config = modules.get("rider_association", {})
                if not self.config:
                    # Fallback to defaults
                    self.config = {
                        "minimum_iou": 0.15,
                        "maximum_distance": 150.0,
                        "association_score_threshold": 0.40,
                        "minimum_confidence": 0.50,
                        "maximum_passengers": 3
                    }
                logger.info("RiderAssociationService configuration loaded.")
            except Exception as e:
                logger.error(f"Failed to load RiderAssociationService config: {e}")
                self.config = {}
        else:
            self.config = {
                "minimum_iou": 0.15,
                "maximum_distance": 150.0,
                "association_score_threshold": 0.40,
                "minimum_confidence": 0.50,
                "maximum_passengers": 3
            }

    def associate_riders(
        self,
        motorcycles: List[Dict[str, Any]],
        riders: List[Dict[str, Any]],
        timestamp: float
    ) -> None:
        """
        Executes a spatial matching pass to associate riders with motorcycles.
        Resets and populates self.motorcycle_groups.
        
        Args:
            motorcycles: List of dicts representing motorcycles:
                         {"id": track_id, "bbox": [x1, y1, x2, y2], "conf": conf}
            riders: List of dicts representing riders (people):
                    {"id": track_id, "bbox": [x1, y1, x2, y2], "conf": conf}
            timestamp: Evaluation frame timestamp
        """
        self.clear_associations()

        min_iou = self.config.get("minimum_iou", 0.15)
        max_dist = self.config.get("maximum_distance", 150.0)
        score_threshold = self.config.get("association_score_threshold", 0.40)

        # 1. Calculate matching scores matrix between all motorcycles and riders
        # Map: rider_idx -> List of Tuple[motorcycle_idx, score]
        rider_matches: Dict[int, List[Tuple[int, float]]] = {}
        
        for r_idx, rider in enumerate(riders):
            r_box = rider["bbox"]
            r_cx = (r_box[0] + r_box[2]) / 2.0
            r_cy = (r_box[1] + r_box[3]) / 2.0
            
            for m_idx, moto in enumerate(motorcycles):
                m_box = moto["bbox"]
                m_cx = (m_box[0] + m_box[2]) / 2.0
                m_cy = (m_box[1] + m_box[3]) / 2.0
                
                # Intersection Over Rider (overlap ratio)
                overlap_ratio = self._calculate_box_overlap(r_box, m_box)
                
                # Center distance
                dist = float(np.sqrt((r_cx - m_cx)**2 + (r_cy - m_cy)**2))
                
                # Weighted score
                if dist < max_dist and overlap_ratio >= min_iou:
                    # Closer distance increases score, max score when dist=0 is 1.0
                    dist_factor = 1.0 - (dist / max_dist)
                    score = (0.60 * overlap_ratio) + (0.40 * dist_factor)
                    
                    if score >= score_threshold:
                        if r_idx not in rider_matches:
                            rider_matches[r_idx] = []
                        rider_matches[r_idx].append((m_idx, score))

        # 2. Resolve ambiguous matches (each rider belongs to the motorcycle with the highest score)
        # Map: motorcycle_idx -> List of rider dicts
        moto_associations: Dict[int, List[Dict[str, Any]]] = {idx: [] for idx in range(len(motorcycles))}
        
        for r_idx, matches in rider_matches.items():
            # Sort by score descending and take highest match
            matches.sort(key=lambda x: x[1], reverse=True)
            best_m_idx, _ = matches[0]
            moto_associations[best_m_idx].append(riders[r_idx])

        # 3. Create MotorcycleGroup for each motorcycle
        for m_idx, moto in enumerate(motorcycles):
            m_id = moto["id"]
            m_box = moto["bbox"]
            m_conf = moto["conf"]
            
            associated_riders = moto_associations[m_idx]
            if not associated_riders:
                # No riders found on this motorcycle
                self.motorcycle_groups[m_id] = MotorcycleGroup(
                    motorcycle_tracking_id=m_id,
                    motorcycle_bbox=m_box,
                    timestamp=timestamp,
                    confidence=float(m_conf),
                    rider_count=0
                )
                continue

            # 4. Sort riders from front to back to classify Driver vs Passengers
            # Check flow direction from TrajectoryService heading vector
            heading_vector = trajectory_service.get_motion_vector(m_id)
            dy = heading_vector[1]
            
            # Default sorting: front of motorcycle is at the bottom (dy > 0, descending y)
            # if moving up the screen (dy < 0), front of motorcycle is at the top (ascending y)
            reverse_y_sort = True
            if dy < 0:
                reverse_y_sort = False
                
            # Sort riders by center y-coordinate
            associated_riders.sort(key=lambda r: (r["bbox"][1] + r["bbox"][3]) / 2.0, reverse=reverse_y_sort)

            # Map to RiderInfo objects
            rider_infos: List[RiderInfo] = []
            for pos_idx, rider in enumerate(associated_riders):
                r_type = "driver" if pos_idx == 0 else "passenger"
                rider_infos.append(RiderInfo(
                    rider_tracking_id=rider["id"],
                    rider_type=r_type,
                    bounding_box=rider["bbox"],
                    confidence=float(rider["conf"]),
                    position_index=pos_idx
                ))

            driver = rider_infos[0]
            passengers = rider_infos[1:]

            self.motorcycle_groups[m_id] = MotorcycleGroup(
                motorcycle_tracking_id=m_id,
                motorcycle_bbox=m_box,
                driver=driver,
                passengers=passengers,
                rider_count=len(rider_infos),
                confidence=float(m_conf),
                timestamp=timestamp
            )

    def _calculate_box_overlap(self, box_a: List[float], box_b: List[float]) -> float:
        """Calculates area of intersection / area of box_a."""
        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b

        ix1 = max(ax1, bx1)
        iy1 = max(ay1, by1)
        ix2 = min(ax2, bx2)
        iy2 = min(ay2, by2)

        if ix1 < ix2 and iy1 < iy2:
            intersection_area = (ix2 - ix1) * (iy2 - iy1)
            box_a_area = (ax2 - ax1) * (ay2 - ay1)
            if box_a_area > 0:
                return intersection_area / box_a_area
        return 0.0

    # ── Public APIs ───────────────────────────────────────────────────────────

    def get_motorcycle_group(self, motorcycle_id: int) -> Optional[MotorcycleGroup]:
        """Retrieves the complete MotorcycleGroup details for a motorcycle ID."""
        return self.motorcycle_groups.get(motorcycle_id)

    def get_driver(self, motorcycle_id: int) -> Optional[RiderInfo]:
        """Retrieves the driver of the motorcycle."""
        group = self.get_motorcycle_group(motorcycle_id)
        return group.driver if group else None

    def get_passengers(self, motorcycle_id: int) -> List[RiderInfo]:
        """Retrieves list of passengers on the motorcycle."""
        group = self.get_motorcycle_group(motorcycle_id)
        return group.passengers if group else []

    def get_rider_count(self, motorcycle_id: int) -> int:
        """Retrieves total count of riders associated with the motorcycle."""
        group = self.get_motorcycle_group(motorcycle_id)
        return group.rider_count if group else 0

    def get_primary_rider(self, motorcycle_id: int) -> Optional[RiderInfo]:
        """Alias for get_driver."""
        return self.get_driver(motorcycle_id)

    def get_secondary_riders(self, motorcycle_id: int) -> List[RiderInfo]:
        """Alias for get_passengers."""
        return self.get_passengers(motorcycle_id)

    def validate_association(self, motorcycle_id: int) -> bool:
        """Validates if the motorcycle has an associated driver."""
        driver = self.get_driver(motorcycle_id)
        return driver is not None

    def clear_associations(self) -> None:
        """Clears all cached associations."""
        self.motorcycle_groups.clear()

    def reset(self) -> None:
        """Resets the service state."""
        self.clear_associations()


# Global singleton instance
rider_association_service = RiderAssociationService()
