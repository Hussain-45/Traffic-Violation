"""
Plate Recognition Service
=========================
Manages OCR candidate management, Indian registration validation regex rules,
text normalization (OCR confusion replacement), multi-frame voting, and stable plate outputs.
"""
import os
import re
import yaml
from collections import Counter
from typing import List, Dict, Tuple, Any, Optional
from loguru import logger

from shared.schemas.plate_recognition import OCRCandidate, PlateRecognitionState


class PlateRecognitionService:
    """
    Service layer responsible for OCR text voting, validation, and history aggregation.
    """

    def __init__(self, pipeline_config_path: str = "configs/pipeline.yaml"):
        self.pipeline_config_path = pipeline_config_path
        self.config: Dict[str, Any] = {}
        # Map: vehicle_tracking_id -> PlateRecognitionState
        self.recognition_states: Dict[int, PlateRecognitionState] = {}
        self.load_config()

        # Compile validation regex patterns
        # Standard: MH12AB1234, DL8CAF5032, PB10XY4567, HR26DK8337, KA01AB0001
        self.standard_pattern = re.compile(r"^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}$")
        # Loose format (for partials/customs): MH12A1234, MH121234, KA010001
        self.loose_pattern = re.compile(r"^[A-Z]{2}[0-9]{1,2}[A-Z]{0,2}[0-9]{1,4}$")

    def load_config(self) -> None:
        """Loads configuration parameters from pipeline.yaml, falling back to defaults."""
        if os.path.exists(self.pipeline_config_path):
            try:
                with open(self.pipeline_config_path, "r") as f:
                    full_cfg = yaml.safe_load(f) or {}
                modules = full_cfg.get("modules", {})
                self.config = modules.get("plate_recognition", {})
                if not self.config:
                    self.config = {
                        "minimum_ocr_confidence": 0.50,
                        "minimum_votes": 3,
                        "minimum_history": 3,
                        "minimum_validation_score": 0.60,
                        "maximum_history": 15,
                        "normalization_rules": True
                    }
                logger.info("PlateRecognitionService configurations loaded.")
            except Exception as e:
                logger.error(f"Failed to load PlateRecognitionService configs: {e}")
                self.config = {}
        else:
            self.config = {
                "minimum_ocr_confidence": 0.50,
                "minimum_votes": 3,
                "minimum_history": 3,
                "minimum_validation_score": 0.60,
                "maximum_history": 15,
                "normalization_rules": True
            }

    def normalize_plate(self, text: str) -> str:
        """
        Cleans OCR text, removes spacing, and resolves common OCR character confusions
        based on character index positions in standard Indian vehicle registrations.
        """
        # Upper case, remove spaces/hyphens/non-alphanumeric
        cleaned = re.sub(r"[^A-Za-z0-9]", "", text).upper()
        
        # Resolve positional OCR confusions if length matches standard Indian format (8 to 10 chars)
        # Standard: AA NN AA NNNN (10 chars), AA NN A NNNN (9 chars), AA NN NNNN (8 chars)
        char_len = len(cleaned)
        if 8 <= char_len <= 10:
            result_chars = []
            
            # Confusion tables
            to_letter = {"0": "O", "1": "I", "5": "S", "8": "B", "2": "Z"}
            to_digit = {"O": "0", "I": "1", "S": "5", "B": "8", "Z": "2", "G": "6", "T": "7"}

            for idx, char in enumerate(cleaned):
                # 1. State Code (Indices 0, 1) -> Must be letters
                if idx in (0, 1):
                    result_chars.append(to_letter.get(char, char))
                # 2. District Code (Indices 2, 3) -> Must be digits
                elif idx in (2, 3):
                    result_chars.append(to_digit.get(char, char))
                # 3. Last 4 characters -> Must be digits
                elif idx >= (char_len - 4):
                    result_chars.append(to_digit.get(char, char))
                # 4. Middle Series Letters -> Must be letters
                else:
                    result_chars.append(to_letter.get(char, char))
            
            return "".join(result_chars)
        
        # Generic confusion fallback
        return cleaned

    def validate_plate(self, text: str) -> str:
        """
        Validates normalized plate text against Indian registration patterns.
        
        Returns:
            "Valid" if standard match, "Possibly Valid" if partial/loose,
            "Invalid" if not matching, "Unknown" if input is empty.
        """
        if not text:
            return "Unknown"
        
        if self.standard_pattern.match(text):
            return "Valid"
        
        if self.loose_pattern.match(text):
            return "Possibly Valid"
            
        # At least 5 alphanumeric characters (safety net for crop text fragments)
        if len(text) >= 5:
            return "Possibly Valid"
            
        return "Invalid"

    def process_ocr_result(
        self,
        vehicle_id: int,
        recognized_text: str,
        confidence: float,
        engine_name: str,
        timestamp: float,
        frame_id: int
    ) -> Optional[PlateRecognitionState]:
        """
        Appends OCR reading, normalizes, validates, updates history, runs voting,
        and computes stable plate text.
        """
        min_ocr_conf = self.config.get("minimum_ocr_confidence", 0.50)
        max_history = self.config.get("maximum_history", 15)
        min_votes = self.config.get("minimum_votes", 3)

        if confidence < min_ocr_conf or not recognized_text:
            return self.recognition_states.get(vehicle_id)

        # 1. Normalize and Validate
        norm_text = self.normalize_plate(recognized_text)
        val_status = self.validate_plate(norm_text)

        candidate = OCRCandidate(
            recognized_text=recognized_text,
            normalized_text=norm_text,
            confidence=confidence,
            engine_name=engine_name,
            timestamp=timestamp,
            frame_id=frame_id
        )

        # 2. Get or initialize state
        if vehicle_id not in self.recognition_states:
            self.recognition_states[vehicle_id] = PlateRecognitionState(
                vehicle_tracking_id=vehicle_id,
                timestamp=timestamp
            )

        state = self.recognition_states[vehicle_id]
        state.timestamp = timestamp
        
        # Avoid duplicate frame entries
        if not state.recognition_history or state.recognition_history[-1].frame_id != frame_id:
            state.recognition_history.append(candidate)
            if len(state.recognition_history) > max_history:
                state.recognition_history.pop(0)

        # 3. Multi-frame Voting & Confidence Aggregation
        # Count frequency of normalized texts
        candidates_texts = [c.normalized_text for c in state.recognition_history]
        text_counts = Counter(candidates_texts)
        
        # Calculate sum of confidence per text
        text_confidence_sums: Dict[str, float] = {}
        for c in state.recognition_history:
            text_confidence_sums[c.normalized_text] = text_confidence_sums.get(c.normalized_text, 0.0) + c.confidence

        # Get winner (highest confidence sum)
        if text_confidence_sums:
            best_text = max(text_confidence_sums, key=text_confidence_sums.get)
            best_conf_sum = text_confidence_sums[best_text]
            vote_count = text_counts[best_text]
            
            # Find the best candidate object in history matching the best_text
            best_obj = max((c for c in state.recognition_history if c.normalized_text == best_text), key=lambda x: x.confidence)
            
            state.best_candidate = best_obj
            state.vote_count = vote_count
            state.validation_status = self.validate_plate(best_text)
            
            # Aggregate confidence score
            avg_conf = best_conf_sum / vote_count
            state.aggregated_confidence = avg_conf

            # 4. Confirm stable plate if voting thresholds satisfied
            if vote_count >= min_votes and state.validation_status != "Invalid":
                if state.stable_plate != best_text:
                    state.stable_plate = best_text
                    logger.info(f"Stable plate established for Vehicle #{vehicle_id}: '{best_text}' (Votes: {vote_count})")
        
        return state

    # ── Public APIs ───────────────────────────────────────────────────────────

    def get_best_candidate(self, vehicle_id: int) -> Optional[OCRCandidate]:
        """Retrieves OCR Candidate representing the highest voting match."""
        state = self.recognition_states.get(vehicle_id)
        return state.best_candidate if state else None

    def get_recognition_state(self, vehicle_id: int) -> Optional[PlateRecognitionState]:
        """Retrieves the complete PlateRecognitionState metadata structure."""
        return self.recognition_states.get(vehicle_id)

    def get_stable_plate(self, vehicle_id: int) -> Optional[str]:
        """Retrieves the confirmed stable plate text string."""
        state = self.recognition_states.get(vehicle_id)
        return state.stable_plate if state else None

    def clear_history(self, vehicle_id: int) -> None:
        """Clears OCR history buffer for a vehicle."""
        self.recognition_states.pop(vehicle_id, None)

    def reset(self) -> None:
        """Resets the complete service mappings."""
        self.recognition_states.clear()


# Global singleton instance
plate_recognition_service = PlateRecognitionService()
