import os
import time
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.app.config import settings
from backend.app.database import engine, Base
from backend.app.routes import auth, violations, cameras, dashboard, analytics, users, settings as settings_routes, locations, reports, fines, notifications
from backend.app.utils.seed import seed_db

# Configure structured system logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("stvds_backend.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("STVDS")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Smart Traffic Violation Detection System",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# Global error exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An unexpected error occurred in the Smart Traffic backend pipeline.",
            "detail": str(exc)
        }
    )

# Request-Response duration logging middleware
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(f"HTTP {request.method} {request.url.path} - Status: {response.status_code} - Duration: {process_time:.2f}ms")
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(f"HTTP {request.method} {request.url.path} failed - Duration: {process_time:.2f}ms - Error: {str(e)}")
        raise e

# Security Headers Middleware setup
@app.middleware("http")
async def add_security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "default-src 'self' http://localhost:8000; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: blob: http://localhost:8000; connect-src 'self' ws://localhost:8000 http://localhost:8000;"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

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
app.include_router(locations.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(fines.router, prefix=settings.API_V1_STR)
app.include_router(notifications.router, prefix=settings.API_V1_STR)

@app.on_event("startup")
def startup_event():
    # Validate environment state
    from backend.app.utils.env_validator import validate_environment
    validate_environment()

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
