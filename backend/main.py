from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from loguru import logger

from backend.app.core.config import settings
from backend.app.core.logging import setup_app_logging
from backend.app.core.middleware import RequestLoggingMiddleware
from backend.app.core.exceptions import register_exception_handlers
from backend.app.api.v1.router import api_router

# Configure logging on module import
setup_app_logging()


from backend.app.database import engine, Base
from backend.app.utils.seed import seed_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Asynchronous lifespan context manager handling app startup and shutdown hooks.
    """
    # Startup actions
    logger.info("=========================================")
    logger.info(f"🚀 Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info("-----------------------------------------")
    logger.info("⚙️ Verifying environment parameters:")
    logger.info(f"   - Database URL: {'[SET]' if settings.DATABASE_URL else '[EMPTY]'}")
    logger.info(
        f"   - Camera Source: {'[SET]' if settings.CAMERA_SOURCE else '[EMPTY]'}"
    )
    logger.info(f"   - YOLO Model: {'[SET]' if settings.YOLO_MODEL else '[EMPTY]'}")
    logger.info("=========================================")

    # Initialize Database Schema & Seed Data
    logger.info("[Startup] Initializing Database Schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("[Startup] Seeding database with demo data...")
    seed_db()
    logger.info("[Startup] Ready to receive traffic signals.")

    yield

    # Shutdown actions
    logger.info("Application stopped successfully.")


# Create FastAPI instance with required metadata and lifespan manager
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Register Centralized Exception Handlers
register_exception_handlers(app)

from fastapi.staticfiles import StaticFiles
app.mount("/data", StaticFiles(directory="data"), name="data")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# Register Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(RequestLoggingMiddleware)

# Register API Router
app.include_router(api_router, prefix=settings.API_V1_STR)


# Root Endpoint
@app.get("/", status_code=status.HTTP_200_OK)
def read_root():
    """
    Root endpoint returning general service status.
    """
    return {"message": "Traffic Violation AI Backend Running"}
