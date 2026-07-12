import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Traffic Violation Detection System"
    API_V1_STR: str = "/api/v1"
    
    # Auth Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database Settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./traffic_system.db")
    
    # Storage Settings
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "data/uploads")
    
    # AI Settings
    # Modes: "active" (real YOLO/OCR if libs installed) or "simulated" (mock for quick demo setup)
    AI_MODE: str = os.getenv("AI_MODE", "active")
    AI_CONFIDENCE_THRESHOLD: float = 0.45
    SPEED_LIMIT_KMH: float = 60.0

    # SMTP Configuration
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_EMAIL: str = os.getenv("SMTP_EMAIL", "coderazze95@gmail.com")
    SMTP_APP_PASSWORD: str = os.getenv("SMTP_APP_PASSWORD", "")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "Traffic Violation AI <coderazze95@gmail.com>")
    EMAIL_MAX_RETRIES: int = int(os.getenv("EMAIL_MAX_RETRIES", "3"))
    EMAIL_RETRY_DELAY: float = float(os.getenv("EMAIL_RETRY_DELAY", "2.0"))

    class Config:
        case_sensitive = True

settings = Settings()

# Create directories if they do not exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "images"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "plates"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "videos"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "videos", "input"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "videos", "output"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_DIR, "videos", "thumbnails"), exist_ok=True)
