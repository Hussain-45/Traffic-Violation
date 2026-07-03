import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.app.config import settings
from backend.app.database import engine, Base
from backend.app.routes import auth, violations, cameras, dashboard, analytics, users, settings as settings_routes
from backend.app.utils.seed import seed_db

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Smart Traffic Violation Detection System",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# CORS Middleware setup
# Enable local React dev server and production domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For demo setup, allow all. Change to specific origins in prod.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads storage directories if they do not exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "images"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "plates"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "videos"), exist_ok=True)

# Mount evidence/uploads directory statically
# This allows the frontend to load images like: http://localhost:8000/data/uploads/images/...
app.mount("/data", StaticFiles(directory="data"), name="data")

# Register routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)
app.include_router(violations.router, prefix=settings.API_V1_STR)
app.include_router(cameras.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(settings_routes.router, prefix=settings.API_V1_STR)

@app.on_event("startup")
def startup_event():
    # Setup tables and seed default dataset
    print("[Startup] Initializing Database Schema...")
    Base.metadata.create_all(bind=engine)
    print("[Startup] Seeding database with demo data...")
    seed_db()
    print("[Startup] Ready to receive traffic signals.")

@app.get("/")
def read_root():
    return {
        "status": "online",
        "system": settings.PROJECT_NAME,
        "version": "1.0.0",
        "api_docs": "/docs"
    }
