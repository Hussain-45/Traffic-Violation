"""
Permission Registry
===================
Declares centralized, standard permission string tokens as constant variables.
"""
from typing import Set


class PermissionRegistry:
    # Standard Permission Scopes
    DASHBOARD_VIEW = "dashboard"
    ANALYTICS_VIEW = "analytics"
    REPORTS_VIEW = "reports"
    EVIDENCE_VIEW = "evidence"
    EMAIL_MANAGE = "email"
    SETTINGS_WRITE = "settings"
    USER_MANAGE = "users"
    CAMERA_MANAGE = "cameras"
    SYSTEM_LOGS = "system_logs"
    SYSTEM_HEALTH = "system_health"
    VIOLATION_REVIEW = "violation_review"
    CONFIGURATION_EDIT = "configuration"
    EXPORTS_DOWNLOAD = "exports"

    @classmethod
    def get_all_permissions(cls) -> Set[str]:
        """Collects all registered permissions in the registry."""
        return {
            cls.DASHBOARD_VIEW,
            cls.ANALYTICS_VIEW,
            cls.REPORTS_VIEW,
            cls.EVIDENCE_VIEW,
            cls.EMAIL_MANAGE,
            cls.SETTINGS_WRITE,
            cls.USER_MANAGE,
            cls.CAMERA_MANAGE,
            cls.SYSTEM_LOGS,
            cls.SYSTEM_HEALTH,
            cls.VIOLATION_REVIEW,
            cls.CONFIGURATION_EDIT,
            cls.EXPORTS_DOWNLOAD,
        }
