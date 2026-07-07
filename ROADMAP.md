# Traffic Violation AI - Development Roadmap

This document outlines the phased roadmap for building and deploying the Traffic Violation AI system.

## Phase 1: Data Preparation & Conversion
- [ ] Write conversion script `xml_to_yolo.py` to convert `number_plate` Pascal VOC XML annotations to standard YOLO TXT format.
- [ ] Write conversion script `coco_to_yolo.py` to convert `traffic_light` JSON annotations to YOLO format.
- [ ] Fix class mismatches and coordinate formatting for the `seat_belt` dataset.
- [ ] Deduplicate datasets to ensure data integrity during model training.

## Phase 2: Model Training & Evaluation
- [ ] Train YOLOv8 object detection model for general traffic violations (`computer_vision`).
- [ ] Train YOLOv8 object detection model for helmet usage (`helmet`).
- [ ] Train YOLOv8 object detection model for seat belt compliance (`seat_belt`).
- [ ] Train YOLOv8 object detection model for license plate detection (`number_plate`).
- [ ] Train CRNN/PaddleOCR model for license plate text reading (`number_plate_ocr`).
- [ ] Evaluate models and compile training metrics.

## Phase 3: Backend API Development (FastAPI)
- [ ] Implement file upload handlers in FastAPI for staging raw media.
- [ ] Write service wrapper classes for running model inference on uploaded images/videos.
- [ ] Design and set up SQLite database schema to log violations (Timestamp, Location, Violation Type, Vehicle Plate, Confidence, Image Link).
- [ ] Develop database REST endpoints (GET violation log, POST new log, GET statistics).
- [ ] Set up auto-generation of PDF/CSV violation reports.

## Phase 4: Frontend Development (Next.js)
- [ ] Build a modern Web Dashboard using Next.js/React and Tailwind CSS.
- [ ] Integrate real-time violation monitoring feed.
- [ ] Create interactive page to upload videos/images and visualize detections in real-time (bounding box overlays).
- [ ] Create violation logs search page with filters (Date, Violation Type, Plate Number) and export options (PDF/CSV).
- [ ] Build analytics graphs (Violations over time, distribution by type).