"""
Plate Association Service
==========================
Associates detected number plates with tracked vehicles using spatial overlap,
distance metrics, and temporal consistency. Computes stable plate historical references.
"""
import os
import yaml
import numpy as np
from typing import List, Dict, Tuple, Any, Optional
from loguru import logger

from shared.schemas.plate_association import PlateInfo, VehiclePlateAssociation


class PlateAssociationService:
    """
    Manages vehicle-to-plate mapping and temporal tracking stability.
    """

    def __init__(self, pipeline_config_path: str = "configs/pipeline.yaml"):
        self.pipeline_config_path = pipeline_config_path
        self.config: Dict[str, Any] = {}
        # Map: vehicle_tracking_id -> VehiclePlateAssociation
        self.associations: Dict[int, VehiclePlateAssociation] = {}
        self.load_config()

    def load_config(self) -> None:
        """Loads configuration from pipeline.yaml, falling back to safe defaults."""
        if os.path.exists(self.pipeline_config_path):
            try:
                with open(self.pipeline_config_path, "r") as f:
                    full_cfg = yaml.safe_load(f) or {}
                modules = full_cfg.get("modules", {})
                self.config = modules.get("plate_association", {})
                if not self.config:
                    self.config = {
                        "minimum_plate_confidence": 0.50,
                        "minimum_association_score": 0.35,
                        "minimum_history_length": 3,
                        "stable_confirmation_frames": 5,
                        "maximum_plate_distance": 150.0,
                        "association_weights": {
                            "overlap": 0.60,
                            "distance": 0.40
                        }
                    }
                logger.info("PlateAssociationService configuration loaded.")
            except Exception as e:
                logger.error(f"Failed to load PlateAssociationService configs: {e}")
                self.config = {}
        else:
            self.config = {
                "minimum_plate_confidence": 0.50,
                "minimum_association_score": 0.35,
                "minimum_history_length": 3,
                "stable_confirmation_frames": 5,
                "maximum_plate_distance": 150.0,
                "association_weights": {
                    "overlap": 0.60,
                    "distance": 0.40
                }
            }

    def associate_all(
        self,
        vehicles: List[Dict[str, Any]],
        plates: List[Dict[str, Any]],
        timestamp: float,
        frame_id: int
    ) -> None:
        """
        Performs a temporal matching pass of detected plates to vehicles.
        
        Args:
            vehicles: List of dicts representing vehicles:
                      {"id": tracking_id, "bbox": [x1, y1, x2, y2], "class_id": cls, "conf": conf}
            plates: List of dicts representing plates:
                    {"id": Optional[int], "bbox": [x1, y1, x2, y2], "conf": conf, "cropped_image": Optional[np.ndarray]}
            timestamp: Evaluation frame timestamp
            frame_id: Evaluation frame index
        """
        min_conf = self.config.get("minimum_plate_confidence", 0.50)
        min_score = self.config.get("minimum_association_score", 0.35)
        max_dist = self.config.get("maximum_plate_distance", 150.0)
        weights = self.config.get("association_weights", {"overlap": 0.60, "distance": 0.40})
        w_overlap = weights.get("overlap", 0.60)
        w_dist = weights.get("distance", 0.40)
        
        stable_confirmations = self.config.get("stable_confirmation_frames", 5)

        # Map: plate_idx -> List of Tuple[vehicle_idx, score]
        plate_matches: Dict[int, List[Tuple[int, float]]] = {}

        for p_idx, plate in enumerate(plates):
            if plate["conf"] < min_conf:
                continue
            
            p_box = plate["bbox"]
            p_cx = (p_box[0] + p_box[2]) / 2.0
            p_cy = (p_box[1] + p_box[3]) / 2.0

            for v_idx, vehicle in enumerate(vehicles):
                v_box = vehicle["bbox"]
                v_cx = (v_box[0] + v_box[2]) / 2.0
                v_cy = (v_box[1] + v_box[3]) / 2.0

                # Bounding Box Overlap (Plate inside Vehicle)
                overlap_ratio = self._calculate_box_overlap(p_box, v_box)

                # Center distance
                dist = float(np.sqrt((p_cx - v_cx)**2 + (p_cy - v_cy)**2))

                if dist < max_dist:
                    dist_factor = 1.0 - (dist / max_dist)
                    score = (w_overlap * overlap_ratio) + (w_dist * dist_factor)

                    if score >= min_score:
                        if p_idx not in plate_matches:
                            plate_matches[p_idx] = []
                        plate_matches[p_idx].append((v_idx, score))

        # Resolve ambiguous matches (each plate assigned to vehicle with highest score)
        vehicle_matches: Dict[int, Tuple[Dict[str, Any], float]] = {}
        for p_idx, matches in plate_matches.items():
            matches.sort(key=lambda x: x[1], reverse=True)
            best_v_idx, best_score = matches[0]
            
            # Check if this vehicle is already matched with a better plate
            if best_v_idx in vehicle_matches:
                prev_plate, prev_score = vehicle_matches[best_v_idx]
                if best_score > prev_score:
                    vehicle_matches[best_v_idx] = (plates[p_idx], best_score)
            else:
                vehicle_matches[best_v_idx] = (plates[p_idx], best_score)

        # Track active vehicle IDs to clean up stale history/records
        active_vehicle_ids = [v["id"] for v in vehicles]

        # Update or insert associations
        for v_idx, vehicle in enumerate(vehicles):
            v_id = vehicle["id"]
            v_box = vehicle["bbox"]
            v_class = vehicle["class_id"]

            if v_idx in vehicle_matches:
                matched_plate, score = vehicle_matches[v_idx]
                plate_info = PlateInfo(
                    plate_tracking_id=matched_plate.get("id"),
                    plate_bbox=matched_plate["bbox"],
                    confidence=float(matched_plate["conf"]),
                    cropped_plate_image=matched_plate.get("cropped_image"),
                    timestamp=timestamp,
                    frame_id=frame_id
                )

                if v_id in self.associations:
                    assoc = self.associations[v_id]
                    assoc.associated_plate = plate_info
                    assoc.association_confidence = score
                    assoc.vehicle_bbox = v_box
                    assoc.timestamp = timestamp
                    
                    # Prevent duplicates in history from the exact same frame
                    if not assoc.plate_history or assoc.plate_history[-1].frame_id != frame_id:
                        assoc.plate_history.append(plate_info)
                        if len(assoc.plate_history) > 15: # limit history buffer
                            assoc.plate_history.pop(0)
                else:
                    self.associations[v_id] = VehiclePlateAssociation(
                        vehicle_tracking_id=v_id,
                        vehicle_class=int(v_class),
                        vehicle_bbox=v_box,
                        associated_plate=plate_info,
                        association_confidence=score,
                        plate_history=[plate_info],
                        timestamp=timestamp
                    )
            else:
                # No plate found for this vehicle in the current frame
                if v_id in self.associations:
                    assoc = self.associations[v_id]
                    assoc.associated_plate = None
                    assoc.association_confidence = 0.0
                    assoc.vehicle_bbox = v_box
                    assoc.timestamp = timestamp

            # Compute stable plate from history
            if v_id in self.associations:
                assoc = self.associations[v_id]
                if len(assoc.plate_history) >= stable_confirmations:
                    # Select highest confidence plate in history
                    assoc.stable_plate = max(assoc.plate_history, key=lambda p: p.confidence)

        # Cleanup stale history for vehicles that left the frame
        self._cleanup_stale_associations(active_vehicle_ids)

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

    def _cleanup_stale_associations(self, active_ids: List[int]) -> None:
        """Removes associations for vehicles that are no longer tracked."""
        for vid in list(self.associations.keys()):
            if vid not in active_ids:
                self.associations.pop(vid, None)

    # ── Public APIs ───────────────────────────────────────────────────────────

    def get_vehicle_plate(self, vehicle_id: int) -> Optional[PlateInfo]:
        """Retrieves the plate currently associated in the active frame."""
        assoc = self.associations.get(vehicle_id)
        return assoc.associated_plate if assoc else None

    def get_plate_history(self, vehicle_id: int) -> List[PlateInfo]:
        """Retrieves the historical associated plate detections list."""
        assoc = self.associations.get(vehicle_id)
        return assoc.plate_history if assoc else []

    def get_stable_plate(self, vehicle_id: int) -> Optional[PlateInfo]:
        """Retrieves the confirmed stable plate details."""
        assoc = self.associations.get(vehicle_id)
        return assoc.stable_plate if assoc else None

    def get_association(self, vehicle_id: int) -> Optional[VehiclePlateAssociation]:
        """Retrieves the complete VehiclePlateAssociation structure."""
        return self.associations.get(vehicle_id)

    def clear_association(self, vehicle_id: int) -> None:
        """Clears the association record for a vehicle ID."""
        self.associations.pop(vehicle_id, None)

    def reset(self) -> None:
        """Resets the complete service mapping state."""
        self.associations.clear()


# Global singleton instance
plate_association_service = PlateAssociationService()
