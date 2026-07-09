"""
Database Service Layer
======================
Handles session transactions, connection retries, error recovery, and idempotent writes.
"""
import time
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from loguru import logger

from backend.app.database import SessionLocal, engine
from backend.app.repositories.evidence_repository import EvidenceRepository
from backend.app.schemas.evidence_schema import EvidenceCreate, EvidenceUpdate, EvidenceResponse
from shared.schemas.evidence_record import EvidenceRecord


class DatabaseService:
    """
    Central service coordinating transaction safety, error handling, and idempotent writes.
    """

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def get_session(self) -> Session:
        """Create and return a new database session."""
        logger.debug("Connection Opened")
        return SessionLocal()

    def close_session(self, db: Session) -> None:
        """Safely close a database session."""
        try:
            db.close()
            logger.debug("Connection Closed")
        except Exception as e:
            logger.error(f"Error closing session: {e}")

    def insert_evidence(self, record: EvidenceRecord) -> Optional[EvidenceResponse]:
        """
        Inserts an EvidenceRecord idempotently.
        If a record with the same evidence_id or hash already exists, returns it directly.
        """
        db = self.get_session()
        repo = EvidenceRepository(db)

        # Idempotence Check 1: By unique evidence_id
        existing = repo.get_by_evidence_id(record.evidence_id)
        if existing:
            logger.info(f"Duplicate Skipped: Record with evidence_id {record.evidence_id} already exists.")
            res = EvidenceResponse.model_validate(existing)
            self.close_session(db)
            return res

        # Idempotence Check 2: By unique file hash
        existing_hash = repo.get_by_hash(record.hash)
        if existing_hash:
            logger.info(f"Duplicate Skipped: Record with hash {record.hash} already exists.")
            res = EvidenceResponse.model_validate(existing_hash)
            self.close_session(db)
            return res

        schema = EvidenceCreate(
            evidence_id=record.evidence_id,
            violation_id=record.violation_id,
            tracking_id=record.tracking_id,
            verified_plate=record.verified_plate,
            vehicle_class=record.vehicle_class,
            violation_type=record.violation_type,
            severity=record.severity,
            timestamp=record.timestamp,
            frame_id=record.frame_id,
            camera_id=record.camera_id,
            location=record.location,
            confidence=record.confidence,
            original_frame_path=record.original_frame_path,
            annotated_frame_path=record.annotated_frame_path,
            vehicle_crop_path=record.vehicle_crop_path,
            plate_crop_path=record.plate_crop_path,
            hash=record.hash,
            metadata=record.metadata
        )

        for attempt in range(1, self.max_retries + 1):
            try:
                db_obj = repo.create(schema)
                db.commit()
                
                logger.info(f"Record Inserted: Evidence ID {record.evidence_id}")
                res = EvidenceResponse.model_validate(db_obj)
                self.close_session(db)
                return res

            except Exception as e:
                db.rollback()
                logger.warning(f"Transaction Rollback: Attempt {attempt}/{self.max_retries} failed: {e}")
                if attempt == self.max_retries:
                    logger.error(f"Error: Failed to insert Evidence Record {record.evidence_id} after {self.max_retries} attempts.")
                    self.close_session(db)
                    return None
                time.sleep(self.retry_delay)

        self.close_session(db)
        return None

    def fetch_evidence(self, evidence_id: str) -> Optional[EvidenceResponse]:
        """Fetch a single record by evidence_id."""
        db = self.get_session()
        repo = EvidenceRepository(db)
        try:
            db_obj = repo.get_by_evidence_id(evidence_id)
            if db_obj:
                return EvidenceResponse.model_validate(db_obj)
            return None
        except Exception as e:
            logger.error(f"Failed to fetch evidence {evidence_id}: {e}")
            return None
        finally:
            self.close_session(db)

    def update_evidence(self, id: int, schema: EvidenceUpdate) -> Optional[EvidenceResponse]:
        """Update an existing record inside a transaction."""
        db = self.get_session()
        repo = EvidenceRepository(db)
        try:
            db_obj = repo.update(id, schema)
            db.commit()
            if db_obj:
                logger.info(f"Record Updated: Primary Key {id}")
                return EvidenceResponse.model_validate(db_obj)
            return None
        except Exception as e:
            db.rollback()
            logger.error(f"Transaction Rollback: Failed to update primary key {id}: {e}")
            return None
        finally:
            self.close_session(db)

    def delete_evidence(self, id: int) -> bool:
        """Delete a record inside a transaction."""
        db = self.get_session()
        repo = EvidenceRepository(db)
        try:
            success = repo.delete(id)
            db.commit()
            if success:
                logger.info(f"Record Deleted: Primary Key {id}")
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Transaction Rollback: Failed to delete primary key {id}: {e}")
            return False
        finally:
            self.close_session(db)

    def search_evidence(
        self,
        plate: Optional[str] = None,
        violation_type: Optional[str] = None,
        severity: Optional[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List[EvidenceResponse], int]:
        db = self.get_session()
        repo = EvidenceRepository(db)
        try:
            results, count = repo.search_and_paginate(plate, violation_type, severity, page, page_size)
            responses = [EvidenceResponse.model_validate(obj) for obj in results]
            return responses, count
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return [], 0
        finally:
            self.close_session(db)

    def get_statistics(self) -> Dict[str, Any]:
        db = self.get_session()
        repo = EvidenceRepository(db)
        try:
            return repo.get_statistics()
        except Exception as e:
            logger.error(f"Failed to query database statistics: {e}")
            return {"total_records": 0, "violations_breakdown": {}, "severity_breakdown": {}}
        finally:
            self.close_session(db)

    def health_check(self) -> bool:
        """Verify the database connection is open and responsive."""
        db = self.get_session()
        try:
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
        finally:
            self.close_session(db)


# Singleton instance
database_service = DatabaseService()
