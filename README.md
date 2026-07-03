# 🚦 Smart Traffic Violation Detection System (STVDS)

A next-generation, high-performance intelligent transportation command system powered by **YOLOv8** and **EasyOCR** for automated vehicle target classification, licence plate recognition, traffic infraction tracking, live camera monitoring, interactive map analytics, and automated fine tariff management.

---

## ⚡ Key Features

1. **AI Vehicle & Licence Plate Recognition**:
   - Automated vehicle segmentation (Cars, Motorcycles, Trucks, Buses, Auto-rickshaws).
   - High-fidelity Licence Plate OCR cropping and translation.
2. **8 Core AI Infraction Classifiers**:
   - No Helmet detection, Seatbelt checks, Triple riding, Wrong-lane driving, Wrong-direction alerts, Stop-line crossing detection, Red light violations, and Illegal parking detection.
3. **Live CCTV Command Desk**:
   - Supports local webcams, RTSP stream URLs, and simulated junction streams.
   - Real-time bounding boxes, live FPS monitors, and camera link toggles.
4. **10 Advanced AI Scanner Tools**:
   - **Night Vision Filter**: CSS-based green infrared thermal lens enhancement.
   - **Weather Sensor Overlays**: Dynamic canvas rain particles and fog filters.
   - **Pedestrian Face Blur**: Automatic anonymization for privacy.
   - **Road Damage Detector**: Live scanning of road lane cracks and potholes.
   - **Stolen Vehicle Alarm**: Database checks that trigger critical cruiser intercepts.
   - **Emergency приоритет**: Prioritizes emergency vehicles (Ambulance, Fire, Police).
5. **Interactive GIS Hotspot Map**:
   - Displays geolocated cameras, violation markers, Delhi NCR sector risk heatmaps, and danger zones.
6. **Analytics & Reporting Desk**:
   - 7 interactive charts displaying peak hours, monthly trends, and revenue metrics.
   - Data compilation with PDF generation and Pandas Excel/CSV exporters.
7. **Fine challan & notifications system**:
   - Automatic fine generation, UPI/Cash payment settlements, and official receipts.
   - Real-time Topbar alert trays and full notifications history lists.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10, FastAPI, SQLite (SQLAlchemy ORM), YOLOv8 (Ultralytics), EasyOCR, Pandas, OpenPyXL.
- **Frontend**: React 18, TypeScript, TailwindCSS, Lucide-React, Framer Motion, Chart.js.
- **Orchestration**: Docker, Docker Compose, Nginx.

---

## 🚀 Quick Start (Local Setup)

### Prerequisites
- Python 3.10+
- Node.js 18+

### 1. Run the Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
The backend API documentation will be available at `http://localhost:8000/docs`.

### 2. Run the Frontend
```bash
cd frontend
npm install
npm run dev
```
Open your browser at `http://localhost:5173`.

---

## 🐳 Docker Deployment

To spin up the entire production environment (FastAPI API service at port `8000` and React Nginx SPA at port `3000`) in one command:

```bash
docker-compose up --build -d
```

---

## 📡 Core API Routes

- **Authentication**: `POST /api/v1/auth/login`, `POST /api/v1/auth/register`
- **Violations**: `GET /api/v1/violations`, `POST /api/v1/violations/upload`
- **Cameras**: `GET /api/v1/cameras`, `POST /api/v1/cameras`
- **Fine Management**: `GET /api/v1/fines/rules`, `PUT /api/v1/fines/rules/{type}`, `POST /api/v1/fines/{id}/pay`
- **Notifications**: `GET /api/v1/notifications`, `PUT /api/v1/notifications/read-all`
