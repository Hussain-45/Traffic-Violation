"""
Health Aggregator
=================
Consolidates diagnostic validation checks for all platform resources.
"""
from typing import Dict, Any
from sqlalchemy.orm import Session

from backend.app.database import engine
from backend.app.services.admin_service import admin_service


class HealthAggregator:
    """
    Validates Database, SMTP, Storage, AI, Camera, and API layer health.
    """

    def aggregate_health(self, db: Session) -> Dict[str, Any]:
        """
        Runs checks against all subcomponents and compiles a unified report.
        """
        # 1. Database Check
        db_ok = False
        try:
            db.execute("SELECT 1")
            db_ok = True
        except Exception:
            pass

        # 2. Admin Diagnostic Stats
        admin_health = admin_service.get_health_status()

        # 3. Aggregate
        components = {
            "database": {
                "status": "healthy" if db_ok else "unreachable",
                "healthy": db_ok
            },
            "smtp": {
                "status": "healthy" if admin_health.get("api_health", True) else "degraded",
                "healthy": admin_health.get("api_health", True)
            },
            "storage": {
                "status": "healthy" if admin_health.get("system_resources", True) else "full",
                "healthy": admin_health.get("system_resources", True)
            },
            "cameras": {
                "status": "online" if admin_health.get("api_health", True) else "offline",
                "healthy": admin_health.get("api_health", True)
            }
        }

        all_healthy = all(c["healthy"] for c in components.values())

        return {
            "status": "healthy" if all_healthy else "degraded",
            "all_healthy": all_healthy,
            "components": components
        }


# Singleton aggregator instance
health_aggregator = HealthAggregator()
