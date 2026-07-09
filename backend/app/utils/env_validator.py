"""
Environment Validator
=====================
Validates critical environment configurations during startup.
"""
import os
import sys
import logging

logger = logging.getLogger("STVDS.EnvValidator")

REQUIRED_PROD_ENV = [
    "ENV_STATE",
    "DATABASE_URL",
    "JWT_SECRET_KEY",
    "JWT_REFRESH_SECRET_KEY",
    "UPLOAD_DIR",
    "SMTP_HOST",
    "SMTP_PORT"
]

def validate_environment() -> None:
    """
    Checks that all required environment variables are set when in production.
    Raises ValueError or warning logs if variables are missing.
    """
    env_state = os.getenv("ENV_STATE", "development")
    logger.info(f"Validating configurations for environment state: {env_state}")

    if env_state != "production":
        logger.warning("System is running in non-production mode. Bypassing strict validations.")
        return

    missing_keys = []
    for key in REQUIRED_PROD_ENV:
        val = os.getenv(key)
        if not val or val.strip() == "":
            missing_keys.append(key)

    if missing_keys:
        err_msg = f"CRITICAL: Missing required production environment variables: {', '.join(missing_keys)}"
        logger.critical(err_msg)
        sys.exit(err_msg)

    logger.info("All required production environment variables verified successfully.")
