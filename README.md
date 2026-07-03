# 🚦 AI-Powered Smart Traffic Violation Detection System

A production-quality, smart city government dashboard designed for automated traffic violation monitoring, vehicle tracking, license plate recognition (OCR), and fine administration.

---

## 🏗️ Tech Stack

### Frontend
- **React (Vite)**
- **Tailwind CSS** (Custom dark/light themes & glassmorphism configurations)
- **Framer Motion** (Micro-animations, modal entries, layout transitions)
- **Recharts** (Visual graphs for peak hours, traffic trends, and revenues)
- **React Router Dom** (Role-based protected views)
- **Lucide Icons** (Streamlined HUD system icons)

### Backend
- **FastAPI** (High performance, type-safe Python API endpoints)
- **SQLAlchemy** (Object Relational Mapping)
- **Pandas & Openpyxl** (Reporting data formatting and Excel exports)

### Database
- **SQLite** (Default local file-based database for zero-config run)
- **PostgreSQL** (Production-ready container setup)

### AI / ML (Dual-Mode Pipeline)
- **YOLOv8** (Vehicle tracking and signals detections)
- **EasyOCR** (License plate character extraction)
- **OpenCV** (Image overlays, frame captures, and canvas feeds drawing)

---

## 📂 Project Structure

```
Traffic Violation/
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   │   └── detector.py       # YOLOv8 & EasyOCR execution (dual-mode)
│   │   ├── auth/
│   │   │   └── jwt.py            # JWT token verification and pass hashes
│   │   ├── routes/
│   │   │   ├── auth.py           # Login, registry and user profiling
│   │   │   ├── violations.py     # Image/Video uploads & AI trigger CRUDs
│   │   │   ├── cameras.py        # CCTV registration & online controllers
│   │   │   ├── dashboard.py      # Telemetry summary trackers
│   │   │   ├── analytics.py      # Excel exports & charts calculations
│   │   │   ├── users.py          # Admin officer access controls
│   │   │   └── settings.py       # Threshold sliders & tariff modifiers
│   │   ├── config.py             # Settings, directories, thresholds
│   │   ├── database.py           # DB sessions
│   │   ├── models.py             # Database SQLAlchemy Schemas
│   │   ├── utils/
│   │   │   └── seed.py           # Database tables seeder
│   │   └── main.py               # Main entry point & static folder mounts
│   ├── requirements.txt          # Python packages
│   └── Dockerfile                # Backend container script
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── Sidebar.jsx       # Custom collapsible sidebar
│   │   ├── pages/
│   │   │   ├── Login.jsx         # Glassmorphic OAuth2 secure portal
│   │   │   ├── Dashboard.jsx     # Active telemetry stats & logs charts
│   │   │   ├── LiveMonitoring.jsx# Live canvas traffic flow drawing
│   │   │   ├── Upload.jsx        # Drag & drop media file processor
│   │   │   ├── Violations.jsx    # Table grid data search & actions drawer
│   │   │   ├── Analytics.jsx     # CSV/XLSX export & metric desks
│   │   │   ├── Map.jsx           # SVG Delhi sectors coordinates map
│   │   │   ├── Cameras.jsx       # Camera checklist registrations
│   │   │   ├── Users.jsx         # Officer access permissions controls
│   │   │   └── Settings.jsx      # Fine amounts tariff configuration
│   │   ├── App.jsx               # Auth & Theme providers & router
│   │   ├── index.css             # Light/Dark variables & scrollbars
│   │   └── main.jsx              # Vite React entry point
│   ├── index.html                # App template
│   ├── package.json              # Front-end dependencies
│   ├── tailwind.config.js        # CSS classes mappings
│   ├── postcss.config.js         # Tailwind builder config
│   └── Dockerfile                # Frontend Nginx server script
├── docker-compose.yml            # System docker orchestration
├── run.bat                       # Local concurrent batch launcher
└── README.md                     # Documentation
```

---

## 🤖 Dual-Mode AI Pipeline

To ensure the system is completely reliable and works out of the box in CPU-constrained local developer environments, the AI Engine contains a **Dual-Mode execution switcher**:

1. **Active AI Mode** (`AI_MODE=active`): 
   The system attempts to import and initialize the PyTorch-based `ultralytics` (YOLOv8) and `easyocr` packages. It downloads the weights automatically, runs live object bounding box extraction on uploaded images/videos, isolates plates, runs character extraction, and saves cropped assets.
2. **Simulated AI Mode** (`AI_MODE=simulated`): 
   If libraries fail to load (or if manually toggled in settings), the system uses OpenCV to draw moving boxes, calculate speeds, crop deterministic mock license plate regions, and trigger random violations (e.g. speeding, signal jumps) to mock live CCTV monitoring networks.

---

## 🔒 Pre-configured Credentials

The database is automatically pre-populated with default security roles on launch:

| Username | Password | Role | Description |
| :--- | :--- | :--- | :--- |
| **`admin`** | `admin123` | **Admin** | Access to all logs, officer registrations, and system configurations. |
| **`officer`** | `officer123` | **Officer** | Access to dashboards, live camera telemetry, and violation resolution. |

---

## 🚀 How to Run Locally

### 1. Backend Service
Make sure you have Python 3.10+ installed:
```bash
# Navigate to backend
cd backend

# Install dependencies (highly recommended in a virtual environment)
pip install -r requirements.txt

# Start Server
python -m uvicorn app.main:app --reload --port 8000
```
API Documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

### 2. Frontend Development Server
Make sure you have Node.js 18+ installed:
```bash
# Navigate to frontend
cd frontend

# Install packages
npm install

# Run dev server
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🖥️ Running on Windows (One-Click)
Run the `run.bat` file located in the root folder. It will concurrently open two console terminals to launch both servers.

---

## 🐳 Running with Docker
Run the whole system in a containerized environment (orchestrating PostgreSQL, FastAPI, and Nginx for React) with a single command:
```bash
docker-compose up --build
```
- **React Frontend**: [http://localhost](http://localhost) (mapped on standard port 80)
- **FastAPI Backend Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
