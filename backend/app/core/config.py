from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Metadata
    PROJECT_NAME: str = "Traffic Violation AI"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "AI-powered Smart Traffic Violation Detection System"
    API_V1_STR: str = "/api/v1"

    # Environment Variables (with placeholders/fallbacks)
    DATABASE_URL: str = ""
    SMTP_EMAIL: str = ""
    SMTP_PASSWORD: str = ""
    SECRET_KEY: str = ""
    YOLO_MODEL: str = ""
    CAMERA_SOURCE: str = ""

    # Pydantic Settings Configuration
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )


settings = Settings()
