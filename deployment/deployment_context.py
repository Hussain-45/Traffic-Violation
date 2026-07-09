"""
Shared Deployment Context
==========================
Unifies configuration parameters, environment states, and infrastructure coordinates.
"""
import os
import sys
import logging
from typing import Dict, Any, List

logger = logging.getLogger("STVDS.DeploymentContext")


class DeploymentContext:
    """
    Singleton deployment manager enforcing environment safety policies.
    """

    def __init__(self):
        self.env_state = os.getenv("ENV_STATE", "development")
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///traffic_system.db")
        self.upload_dir = os.getenv("UPLOAD_DIR", "data/uploads")
        self.log_file = os.getenv("LOG_FILE", "logs/stvds.log")
        self.smtp_host = os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "25"))

    def get_summary(self) -> Dict[str, Any]:
        """Returns summarized configuration coordinates."""
        return {
            "env_state": self.env_state,
            "database_url": self.database_url,
            "upload_dir": self.upload_dir,
            "log_file": self.log_file,
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
        }

    def verify_writable_directories(self) -> List[str]:
        """
        Verifies that target directories are writable.
        Returns a list of failed folders if any exist.
        """
        failed_paths = []
        target_paths = [self.upload_dir, os.path.dirname(self.log_file) or "."]

        for path in target_paths:
            os.makedirs(path, exist_ok=True)
            if not os.access(path, os.W_OK):
                failed_paths.append(path)

        return failed_paths


# Singleton instance
deployment_context = DeploymentContext()
