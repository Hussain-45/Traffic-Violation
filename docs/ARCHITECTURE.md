# 🏗️ System Architecture Diagram

This document illustrates the multi-tier architectural layout of the **Smart Traffic Violation Detection System (STVDS)**.

---

## 🗺️ Architectural Workflow

The system is organized into four main layers:
1. **Presentation Client Layer**: React single page application styled with Tailwind CSS, utilizing framer-motion transitions and Chart.js graphs.
2. **API Application Gateway**: FastAPI router managing JWT validations, file uploads, static directories, and database transaction queries.
3. **AI Pipeline Core Engine**: OpenCV frame processing, YOLOv8 target classifications, and EasyOCR character segmentation.
4. **Relational Database Storage**: Persisted SQLite/PostgreSQL schemas with performance indices on query search filters.

---

## 🎨 System Architecture Mermaid Representation

```mermaid
graph TD
    %% Presentation Client Layer
    subgraph Client ["presentation client layer (react 18)"]
        UI["React Web App Dashboard"]
        CCTV["Live CCTV Player (HTML5 Canvas)"]
        AUTH_HUD["JWT Token Auth Guard"]
    end

    %% Gateway Layer
    subgraph Gateway ["api gateway layer (fastapi)"]
        API["FastAPI Web Routes Router"]
        LOGS["Request Duration Logger Middleware"]
        ERR_GUARD["Global Exception Interception Handler"]
    end

    %% AI Pipeline Layer
    subgraph AI ["ai processing pipeline (yolov8 + easyocr)"]
        YOLO["YOLOv8 Target Detector"]
        OCR["EasyOCR Licence Plate Recognizer"]
    end

    %% Database Storage Layer
    subgraph DB ["database storage layer (sqlite)"]
        SQL_DB[" traffic_system.db "]
        IDX["Indexes (timestamp, plate, status)"]
    end

    %% Connections
    UI -->|HTTP requests + JWT Header| API
    CCTV -->|RTSP / Webcam frames| YOLO
    API -->|Process uploaded images| YOLO
    YOLO -->|Cropped plate regions| OCR
    OCR -->|Extracted licence text| API
    API -->|Read/Write queries| SQL_DB
    SQL_DB -->|Optimized queries| IDX
    AUTH_HUD -->|Verify login| API
```
