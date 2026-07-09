# Plate Recognition Service

The **Plate Recognition Service** is a central shared service layer responsible for processing raw OCR outputs, normalising character sequences, validating registration formatting rules, and executing multi-frame confidence voting.

---

## 1. Architecture

The service sits directly underneath the Number Plate Detection and OCR layers:

```
            Number Plate Detection (Crops & Associations)
                                │
                                ▼
                       OCR engine (easyOCR / PaddleOCR)
                                │
                                ▼
                   PlateRecognitionService ◄──── Normalise, Validate & Vote
                                │
                                ▼
                 Violation Engine / Database
```

---

## 2. Text Normalisation & OCR Confusion Correction

To eliminate errors from font confusions, character substitutions are dynamically performed on standard Indian plate indexes (MH12AB1234 format):

- **Index 0, 1 (State Code)**: Replaces digits with letters (e.g., `0` -> `O`, `1` -> `I`, `5` -> `S`, `8` -> `B`, `2` -> `Z`).
- **Index 2, 3 (District Code)**: Replaces letters with digits (e.g., `O` -> `0`, `I` -> `1`, `S` -> `5`, `B` -> `8`, `Z` -> `2`, `G` -> `6`, `T` -> `7`).
- **Last 4 Indices (Reg Code)**: Replaces letters with digits (e.g., `O` -> `0`, `I` -> `1`, `S` -> `5`, `B` -> `8`, `Z` -> `2`).
- **Series Code (Middle indices)**: Replaces digits with letters (e.g., `0` -> `O`, `1` -> `I`, `5` -> `S`).

---

## 3. Shared Models

### `OCRCandidate`
- `recognized_text` (`str`): Raw OCR text.
- `normalized_text` (`str`): Normalized text.
- `confidence` (`float`): OCR confidence.
- `engine_name` (`str`): Engine name.
- `timestamp` (`float`): Frame timestamp.
- `frame_id` (`int`): Frame ID.

### `PlateRecognitionState`
- `vehicle_tracking_id` (`int`): Vehicle ID.
- `stable_plate` (`Optional[str]`): Confirmed plate text.
- `recognition_history` (`List[OCRCandidate]`): Historical OCR outputs.
- `best_candidate` (`Optional[OCRCandidate]`): Winner candidate.
- `aggregated_confidence` (`float`): Aggregated confidence score.
- `vote_count` (`int`): Count of matching votes.
- `validation_status` (`str`): Standard Indian format validation status (`Valid`, `Possibly Valid`, `Invalid`).

---

## 4. Multi-frame Voting & Confidence Aggregation

- **Voting**: Calculates the frequency of each distinct normalized string in the vehicle's OCR candidate history.
- **Aggregation**: Computes the sum of confidences for each unique string. The string yielding the highest confidence sum wins.
- **Stable Promotion**: Once a candidate text achieves `minimum_votes = 3` and is not explicitly marked as `Invalid`, it is promoted to `stable_plate`.
