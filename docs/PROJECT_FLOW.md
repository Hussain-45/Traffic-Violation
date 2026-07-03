# 🔄 Project execution Flow Diagram

This document tracks the sequence of events that occur when a camera records a frame containing traffic violations or vehicles.

---

## 🚦 Processing Pipeline Execution Steps

1. **Frame Capture**: CCTV cameras capture video frames. Officers can also upload images/videos manually.
2. **AI Inference Pipeline**:
   - OpenCV decodes the media.
   - YOLOv8 isolates bounding boxes (cars, motorcycles, etc.).
   - EasyOCR reads license plate characters.
3. **Database Checks**:
   - Batch lookups find or create vehicle records.
   - Checks identify if the vehicle status is `"stolen"`.
4. **Tariff Assignment**: The system queries `fine_rules` for detected infraction types to calculate fine amounts.
5. **Incident Persistence**: The infraction is saved to the `violations` table.
6. **Notification Broadcast**: The backend commits a new row to `notifications` (automatically updates Topbar badges).
7. **Response rendering**: The dashboard charts and map components auto-refresh to reflect the new data.

---

## 🎬 Sequence Flow Mermaid Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Officer as User / CCTV Node
    participant UI as React Client Interface
    participant API as FastAPI Router
    participant YOLO as YOLOv8 Target Detector
    participant OCR as EasyOCR Engine
    participant DB as SQLite Database

    Officer->>UI: Upload traffic media / Active stream frame
    UI->>API: POST /api/v1/violations/upload (JWT Auth)
    API->>YOLO: Pass frame for vehicle segmentation
    YOLO-->>API: Returns bounding boxes and coordinates
    API->>OCR: Pass cropped license plate segment
    OCR-->>API: Returns licence plate text string
    API->>DB: Batch query license plate (IN plates)
    DB-->>API: Returns vehicle profiles (stolen check)
    API->>DB: Query fine tariffs for infraction types
    DB-->>API: Returns challan cost values
    API->>DB: INSERT Violation, INSERT Notification (alerts)
    DB-->>API: Confirm commits success
    API-->>UI: Return JSON results (evidence path, speed, alert status)
    UI-->>Officer: Flash HUD warning banner + update chart counters
```
