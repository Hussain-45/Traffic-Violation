"""
Evidence Repository Pattern Implementation
==========================================
Encapsulates all database query logic for Evidence records using SQLAlchemy.
"""
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
import datetime

from backend.app.models.evidence_model import EvidenceModel
from backend.app.schemas.evidence_schema import EvidenceCreate, EvidenceUpdate


class EvidenceRepository:
    """
    Repository class hiding ORM specifics from business/service layers.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, schema: EvidenceCreate) -> EvidenceModel:
        """Create a new Evidence record in the database."""
        db_obj = EvidenceModel(
            evidence_id=schema.evidence_id,
            violation_id=schema.violation_id,
            tracking_id=schema.tracking_id,
            verified_plate=schema.verified_plate,
            vehicle_class=schema.vehicle_class,
            violation_type=schema.violation_type,
            severity=schema.severity,
            timestamp=schema.timestamp,
            frame_id=schema.frame_id,
            camera_id=schema.camera_id,
            location=schema.location,
            confidence=schema.confidence,
            original_frame_path=schema.original_frame_path,
            annotated_frame_path=schema.annotated_frame_path,
            vehicle_crop_path=schema.vehicle_crop_path,
            plate_crop_path=schema.plate_crop_path,
            hash=schema.hash,
            evidence_metadata=schema.evidence_metadata
        )
        self.db.add(db_obj)
        self.db.flush()  # Populates ID without committing transaction
        return db_obj

    def get(self, id: int) -> Optional[EvidenceModel]:
        """Fetch a single record by primary key."""
        return self.db.query(EvidenceModel).filter(EvidenceModel.id == id).first()

    def get_by_evidence_id(self, evidence_id: str) -> Optional[EvidenceModel]:
        """Fetch a single record by unique UUID string."""
        return self.db.query(EvidenceModel).filter(EvidenceModel.evidence_id == evidence_id).first()

    def get_by_hash(self, file_hash: str) -> Optional[EvidenceModel]:
        """Fetch a single record by its file signature hash."""
        return self.db.query(EvidenceModel).filter(EvidenceModel.hash == file_hash).first()

    def update(self, id: int, schema: EvidenceUpdate) -> Optional[EvidenceModel]:
        """Update an existing record's attributes."""
        db_obj = self.get(id)
        if not db_obj:
            return None

        update_data = schema.model_dump(exclude_unset=True)
        for key, val in update_data.items():
            if key == "metadata":
                db_obj.evidence_metadata = val
            else:
                setattr(db_obj, key, val)

        self.db.flush()
        return db_obj

    def delete(self, id: int) -> bool:
        """Delete a record by primary key."""
        db_obj = self.get(id)
        if not db_obj:
            return False
        self.db.delete(db_obj)
        self.db.flush()
        return True

    def find_by_plate(self, plate: str) -> List[EvidenceModel]:
        """Query records by verified license plate text."""
        return self.db.query(EvidenceModel).filter(
            EvidenceModel.verified_plate.like(f"%{plate}%")
        ).all()

    def find_by_tracking_id(self, tracking_id: int) -> List[EvidenceModel]:
        """Query records by vehicle tracker ID."""
        return self.db.query(EvidenceModel).filter(EvidenceModel.tracking_id == tracking_id).all()

    def find_by_violation(self, violation_type: str) -> List[EvidenceModel]:
        """Query records by specific violation type."""
        return self.db.query(EvidenceModel).filter(EvidenceModel.violation_type == violation_type).all()

    def find_by_date(self, start_date: datetime.datetime, end_date: datetime.datetime) -> List[EvidenceModel]:
        """Query records matching a creation date range."""
        return self.db.query(EvidenceModel).filter(
            EvidenceModel.created_at >= start_date,
            EvidenceModel.created_at <= end_date
        ).all()

    def search_and_paginate(
        self,
        plate: Optional[str] = None,
        violation_type: Optional[str] = None,
        severity: Optional[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[EvidenceModel], int]:
        """
        Advanced filtering, search, and pagination.
        Returns a tuple of (results, total_count).
        """
        query = self.db.query(EvidenceModel)

        if plate:
            query = query.filter(EvidenceModel.verified_plate.like(f"%{plate}%"))
        if violation_type:
            query = query.filter(EvidenceModel.violation_type == violation_type)
        if severity:
            query = query.filter(EvidenceModel.severity == severity)

        total_count = query.count()
        results = query.order_by(EvidenceModel.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return results, total_count

    def get_statistics(self) -> Dict[str, Any]:
        """
        Aggregates system-wide evidence metrics.
        """
        total = self.db.query(EvidenceModel).count()
        
        # Violation type breakdown
        type_counts = self.db.query(
            EvidenceModel.violation_type, func.count(EvidenceModel.id)
        ).group_by(EvidenceModel.violation_type).all()
        
        # Severity breakdown
        severity_counts = self.db.query(
            EvidenceModel.severity, func.count(EvidenceModel.id)
        ).group_by(EvidenceModel.severity).all()

        return {
            "total_records": total,
            "violations_breakdown": {t: c for t, c in type_counts},
            "severity_breakdown": {s: c for s, c in severity_counts}
        }
