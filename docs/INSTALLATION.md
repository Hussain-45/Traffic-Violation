# 📥 System Installation Guide

This document outlines the setup and launch configurations for the **Smart Traffic Violation Detection System (STVDS)**.

---

## 📋 System Prerequisites

Ensure you have the following software installed locally:
- **Python**: Version 3.10.x (Recommended)
- **Node.js**: Version 18.x or 20.x (with npm)
- **Git**: For version control cloning
- **Docker & Docker Compose**: (Optional, for containerized deployments)

---

## 🐍 1. Backend Service Configuration

Navigate to the `backend` folder and configure a local virtual environment:

```bash
cd backend

# Create Virtual Environment
python -m venv venv

# Activate Virtual Environment
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies (includes PyTorch, YOLOv8, and EasyOCR)
pip install -r requirements.txt
pip install email-validator
```

### Run database migrations & boot server:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Upon startup, the database `traffic_system.db` will be created automatically and seeded with default admin accounts, camera checkpoints, locations, and fine guidelines.

---

## ⚛️ 2. React Frontend Configuration

Navigate to the `frontend` directory, install packages, and start the Vite dev server:

```bash
cd ../frontend

# Install npm dependencies
npm install

# Start local Vite development server
npm run dev
```
Open **[http://localhost:5173/](http://localhost:5173/)** to access the dashboard.

---

## 🐳 3. Containerized Orchestration (Docker)

To build and launch the integrated FastAPI, React, and Nginx stack:

```bash
# From the project root containing docker-compose.yml
docker-compose up --build -d
```
- **Cockpit Client URL**: `http://localhost:3000`
- **Backend API Gateway**: `http://localhost:8000/docs`
