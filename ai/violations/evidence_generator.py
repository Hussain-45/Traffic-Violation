"""
Evidence Generator
==================
Generates self-contained EvidenceRecord packages from confirmed ViolationRecord
inputs by cropping vehicles and license plates from the original frame, saving
original and annotated frames, and computing SHA-256 integrity hashes.
"""
import os
import uuid
import yaml
import cv2
import hashlib
from typing import Dict, Any, List, Optional
from loguru import logger

from shared.schemas.violation_record import ViolationRecord
from shared.schemas.evidence_record import EvidenceRecord
from ai.pipelines.pipeline_context import PipelineContext


class EvidenceGenerator:
    """
    Decoupled business layer that constructs evidence packages.
    """

    def __init__(self, pipeline_config_path: str = "configs/pipeline.yaml"):
        self.pipeline_config_path = pipeline_config_path
        self.output_dir = "outputs/evidence"
        self.image_format = "jpg"
        self.jpeg_quality = 90
        self.camera_id = "CAM_MUM_01"
        self.location = "GPS: 19.0760, 72.8777"
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return

        if os.path.exists(self.pipeline_config_path):
            try:
                with open(self.pipeline_config_path, "r") as f:
                    full_cfg = yaml.safe_load(f) or {}
                cfg = full_cfg.get("modules", {}).get("evidence_generation", {})
                self.output_dir = cfg.get("output_dir", self.output_dir)
                self.image_format = cfg.get("image_format", self.image_format)
                self.jpeg_quality = cfg.get("jpeg_quality", self.jpeg_quality)
                self.camera_id = cfg.get("camera_id", self.camera_id)
                self.location = cfg.get("location", self.location)
            except Exception as e:
                logger.error(f"Failed to load EvidenceGenerator config: {e}")

        os.makedirs(self.output_dir, exist_ok=True)
        self._initialized = True
        logger.info(f"EvidenceGenerator initialized. Outputs: {self.output_dir}")

    def process_evidence(
        self, violation_records: List[ViolationRecord], context: PipelineContext
    ) -> List[EvidenceRecord]:
        """
        Translates a list of violation records into evidence packages.
        """
        if not self._initialized:
            self.initialize()

        evidence_records = []

        # If context doesn't carry a valid frame, we cannot generate crops/evidence images
        if not context.is_valid():
            logger.warning("PipelineContext does not contain valid frame data. Skipping evidence generation.")
            return []

        raw_frame = context.raw_frame
        annotated_frame = context.working_frame if context.working_frame is not None else raw_frame
        img_h, img_w = raw_frame.shape[:2]

        for rec in violation_records:
            try:
                # Evidence package identifier
                evidence_id = str(uuid.uuid4())

                # Paths
                orig_name = f"{evidence_id}_original.{self.image_format}"
                orig_path = os.path.join(self.output_dir, orig_name)

                annotated_name = f"{evidence_id}_annotated.{self.image_format}"
                annotated_path = os.path.join(self.output_dir, annotated_name)

                vehicle_crop_name = f"{evidence_id}_vehicle.{self.image_format}"
                vehicle_crop_path_local = os.path.join(self.output_dir, vehicle_crop_name)

                plate_crop_name = f"{evidence_id}_plate.{self.image_format}"
                plate_crop_path_local = os.path.join(self.output_dir, plate_crop_name)

                # Save original and annotated frames
                cv2.imwrite(orig_path, raw_frame, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
                cv2.imwrite(annotated_path, annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])

                # Crop vehicle
                vehicle_crop_path = None
                vehicle_bbox = None
                if context.tracked_detections is not None:
                    # Find matching tracker_id
                    for i, tracker_id in enumerate(context.tracked_detections.tracker_id):
                        if int(tracker_id) == rec.tracking_id:
                            vehicle_bbox = context.tracked_detections.xyxy[i].tolist()
                            break

                if vehicle_bbox:
                    vx1, vy1, vx2, vy2 = map(int, vehicle_bbox)
                    vcx1 = max(0, vx1)
                    vcy1 = max(0, vy1)
                    vcx2 = min(img_w, vx2)
                    vcy2 = min(img_h, vy2)
                    v_crop = raw_frame[vcy1:vcy2, vcx1:vcx2].copy()
                    if v_crop.size > 0:
                        cv2.imwrite(vehicle_crop_path_local, v_crop, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
                        vehicle_crop_path = vehicle_crop_path_local

                # Crop plate
                plate_crop_path = None
                plate_bbox = None
                plate_det = context.metadata.get("number_plate_detection", {}).get(rec.tracking_id)
                if plate_det:
                    plate_bbox = plate_det.get("metadata", {}).get("plate_bbox")

                if plate_bbox:
                    px1, py1, px2, py2 = map(int, plate_bbox)
                    pcx1 = max(0, px1)
                    pcy1 = max(0, py1)
                    pcx2 = min(img_w, px2)
                    pcy2 = min(img_h, py2)
                    p_crop = raw_frame[pcy1:pcy2, pcx1:pcx2].copy()
                    if p_crop.size > 0:
                        cv2.imwrite(plate_crop_path_local, p_crop, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
                        plate_crop_path = plate_crop_path_local

                # Calculate SHA-256 Hash of the annotated frame for tamper-proofing
                hasher = hashlib.sha256()
                hasher.update(evidence_id.encode('utf-8'))
                if os.path.exists(annotated_path):
                    with open(annotated_path, "rb") as f:
                        hasher.update(f.read())
                integrity_hash = hasher.hexdigest()

                # Construct EvidenceRecord
                ev_rec = EvidenceRecord(
                    evidence_id=evidence_id,
                    violation_id=rec.violation_id,
                    tracking_id=rec.tracking_id,
                    verified_plate=rec.verified_plate,
                    vehicle_class=rec.vehicle_class,
                    violation_type=rec.violation_type,
                    severity=rec.severity,
                    timestamp=rec.timestamp,
                    frame_id=rec.frame_id,
                    camera_id=self.camera_id,
                    location=self.location,
                    confidence=rec.confidence,
                    original_frame_path=orig_path,
                    annotated_frame_path=annotated_path,
                    vehicle_crop_path=vehicle_crop_path,
                    plate_crop_path=plate_crop_path,
                    evidence_status="Generated",
                    hash=integrity_hash,
                    metadata={
                        "camera_id": self.camera_id,
                        "location": self.location,
                        "vehicle_bbox": vehicle_bbox,
                        "plate_bbox": plate_bbox
                    }
                )
                evidence_records.append(ev_rec)
                logger.info(f"Evidence Generated: {evidence_id} for Violation {rec.violation_id}")

            except Exception as e:
                logger.error(f"Failed to generate evidence package for Violation {rec.violation_id}: {e}")

        return evidence_records


# Singleton instance
evidence_generator = EvidenceGenerator()
