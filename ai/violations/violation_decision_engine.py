"""
Violation Decision Engine
=========================
Evaluates VehicleViolationContext inputs against a set of modular business rules
to generate ViolationRecord outputs with appropriate severity levels, aggregated
decision confidence, and duplicate prevention.
"""
import os
import uuid
import yaml
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Set
from loguru import logger

from shared.schemas.violation_context import VehicleViolationContext
from shared.schemas.violation_record import ViolationRecord
from ai.services.violation_aggregation_service import violation_aggregation_service


class BaseViolationRule(ABC):
    """
    Abstract Base Class for all violation evaluation rules.
    """
    @abstractmethod
    def evaluate(self, ctx: VehicleViolationContext, config: Dict[str, Any]) -> List[ViolationRecord]:
        """
        Evaluates a vehicle context and returns any triggered violation records.
        """
        pass

    def create_record(
        self,
        ctx: VehicleViolationContext,
        violation_type: str,
        confidence: float,
        severity: str,
        rule_id: str,
        decision_status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ViolationRecord:
        """
        Helper method to construct a standard ViolationRecord.
        """
        return ViolationRecord(
            violation_id=str(uuid.uuid4()),
            tracking_id=ctx.tracking_id,
            verified_plate=ctx.verified_plate,
            vehicle_class=ctx.vehicle_class,
            violation_type=violation_type,
            severity=severity,
            confidence=confidence,
            timestamp=ctx.timestamp,
            frame_id=ctx.frame_id,
            rule_id=rule_id,
            decision_status=decision_status,
            evidence_required=True,
            metadata=metadata or {}
        )


class HelmetRule(BaseViolationRule):
    def evaluate(self, ctx: VehicleViolationContext, config: Dict[str, Any]) -> List[ViolationRecord]:
        threshold = config.get("helmet_threshold", 0.50)
        severity = config.get("severities", {}).get("helmet", "Medium")
        
        if ctx.helmet_status == "No Helmet":
            status = "Confirmed" if (ctx.stable_detection and ctx.helmet_confidence >= threshold) else "Pending"
            return [self.create_record(ctx, "No Helmet", ctx.helmet_confidence, severity, "RULE_HELMET_01", status)]
        return []


class SeatBeltRule(BaseViolationRule):
    def evaluate(self, ctx: VehicleViolationContext, config: Dict[str, Any]) -> List[ViolationRecord]:
        threshold = config.get("seatbelt_threshold", 0.50)
        severity = config.get("severities", {}).get("seatbelt", "Low")
        
        if ctx.seatbelt_status == "No Seat Belt":
            status = "Confirmed" if (ctx.stable_detection and ctx.seatbelt_confidence >= threshold) else "Pending"
            return [self.create_record(ctx, "No Seat Belt", ctx.seatbelt_confidence, severity, "RULE_SEATBELT_01", status)]
        return []


class MobilePhoneRule(BaseViolationRule):
    def evaluate(self, ctx: VehicleViolationContext, config: Dict[str, Any]) -> List[ViolationRecord]:
        threshold = config.get("phone_threshold", 0.50)
        severity = config.get("severities", {}).get("phone", "Medium")
        
        if ctx.phone_status == "Mobile Phone":
            status = "Confirmed" if (ctx.stable_detection and ctx.phone_confidence >= threshold) else "Pending"
            return [self.create_record(ctx, "Mobile Phone", ctx.phone_confidence, severity, "RULE_PHONE_01", status)]
        return []


class WrongSideRule(BaseViolationRule):
    def evaluate(self, ctx: VehicleViolationContext, config: Dict[str, Any]) -> List[ViolationRecord]:
        threshold = config.get("wrong_side_threshold", 0.50)
        severity = config.get("severities", {}).get("wrong_side", "High")
        
        if ctx.wrong_side_status == "Wrong Side":
            status = "Confirmed" if (ctx.stable_detection and ctx.wrong_side_confidence >= threshold) else "Pending"
            return [self.create_record(ctx, "Wrong Side", ctx.wrong_side_confidence, severity, "RULE_WRONGSIDE_01", status)]
        return []


class TrafficSignalRule(BaseViolationRule):
    def evaluate(self, ctx: VehicleViolationContext, config: Dict[str, Any]) -> List[ViolationRecord]:
        threshold = config.get("signal_threshold", 0.50)
        severity = config.get("severities", {}).get("signal", "Critical")
        
        if ctx.signal_status == "Red Light Jump":
            status = "Confirmed" if (ctx.stable_detection and ctx.signal_confidence >= threshold) else "Pending"
            return [self.create_record(ctx, "Red Light Jump", ctx.signal_confidence, severity, "RULE_SIGNAL_01", status)]
        return []


class TripleRidingRule(BaseViolationRule):
    def evaluate(self, ctx: VehicleViolationContext, config: Dict[str, Any]) -> List[ViolationRecord]:
        threshold = config.get("triple_riding_threshold", 0.50)
        severity = config.get("severities", {}).get("triple_riding", "High")
        
        if ctx.triple_riding_status == "Triple Riding":
            status = "Confirmed" if (ctx.stable_detection and ctx.triple_riding_confidence >= threshold) else "Pending"
            return [self.create_record(ctx, "Triple Riding", ctx.triple_riding_confidence, severity, "RULE_TRIPLE_01", status)]
        return []


class ViolationDecisionEngine:
    """
    Modular engine evaluating vehicle violation contexts against configured rules.
    """

    def __init__(self, pipeline_config_path: str = "configs/pipeline.yaml"):
        self.pipeline_config_path = pipeline_config_path
        self.config: Dict[str, Any] = {}
        # active_violations maps vehicle_tracking_id -> Set of active violation types
        self.active_violations: Dict[int, Set[str]] = {}
        self.rules: List[BaseViolationRule] = [
            HelmetRule(),
            SeatBeltRule(),
            MobilePhoneRule(),
            WrongSideRule(),
            TrafficSignalRule(),
            TripleRidingRule()
        ]
        self._initialized = False

    def initialize(self) -> None:
        if self._initialized:
            return

        if os.path.exists(self.pipeline_config_path):
            try:
                with open(self.pipeline_config_path, "r") as f:
                    full_cfg = yaml.safe_load(f) or {}
                self.config = full_cfg.get("modules", {}).get("violation_engine", {})
            except Exception as e:
                logger.error(f"Failed to load ViolationDecisionEngine config: {e}")
                self.config = {}

        self._initialized = True
        logger.info("ViolationDecisionEngine initialized.")

    def evaluate_vehicle(self, ctx: VehicleViolationContext) -> List[ViolationRecord]:
        """
        Evaluates a single vehicle context against all registered rules,
        applying duplicate prevention and managing the active violation state.
        """
        if not self._initialized:
            self.initialize()

        records = []
        track_id = ctx.tracking_id

        # Setup vehicle active violations track set
        if track_id not in self.active_violations:
            self.active_violations[track_id] = set()

        currently_detected = set()

        for rule in self.rules:
            try:
                rule_records = rule.evaluate(ctx, self.config)
                for rec in rule_records:
                    v_type = rec.violation_type
                    currently_detected.add(v_type)

                    # Only return/issue if it's not already an active confirmed violation
                    if rec.decision_status == "Confirmed":
                        if v_type not in self.active_violations[track_id]:
                            self.active_violations[track_id].add(v_type)
                            records.append(rec)
                            logger.info(f"Violation Decision Created: Vehicle #{track_id} -> {v_type} (Confirmed)")
                    else:
                        # Pending/Rejected states do not lock duplicate state, always report
                        records.append(rec)
            except Exception as e:
                logger.error(f"Error executing rule {rule.__class__.__name__} for Vehicle #{track_id}: {e}")

        # Resolve/clean up resolved violations
        resolved = self.active_violations[track_id] - currently_detected
        for r_type in resolved:
            self.active_violations[track_id].remove(r_type)
            logger.info(f"Violation Decision Resolved: Vehicle #{track_id} -> {r_type} cleared.")

        return records

    def evaluate_all_active(self) -> List[ViolationRecord]:
        """
        Convenience API to evaluate all currently tracked vehicle contexts.
        """
        records = []
        active_contexts = violation_aggregation_service.get_all_contexts()
        
        # Track active vehicle IDs to clean up disappeared vehicle active_violation records
        active_ids = {ctx.tracking_id for ctx in active_contexts}
        for track_id in list(self.active_violations.keys()):
            if track_id not in active_ids:
                del self.active_violations[track_id]

        for ctx in active_contexts:
            records.extend(self.evaluate_vehicle(ctx))

        return records

    def remove_vehicle(self, tracking_id: int) -> None:
        if tracking_id in self.active_violations:
            del self.active_violations[tracking_id]

    def reset(self) -> None:
        self.active_violations.clear()
        logger.info("ViolationDecisionEngine active violations reset.")
