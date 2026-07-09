"""
RBAC Service
============
Handles role permissions checks, authorization logic, and FastAPI route guards.
"""
from typing import List, Set
from fastapi import Depends, HTTPException, status

from backend.app.models import User, Role, Permission
from backend.app.auth.jwt import get_current_user


class RBACService:
    """
    Enforces role and permission constraints for active user sessions.
    """

    def get_user_permissions(self, user: User) -> Set[str]:
        """Collects all unique permission name keys associated with a user."""
        permissions: Set[str] = set()
        
        # 1. Gather permissions from relationships
        for role in user.roles_rel:
            for perm in role.permissions:
                permissions.add(perm.name)
                
        # 2. Add fallback permissions based on text role if roles_rel is empty
        if not permissions and user.role:
            if user.role == "admin":
                permissions.update([
                    "dashboard", "analytics", "reports", "evidence", "email",
                    "settings", "users", "cameras", "system_logs", "system_health",
                    "violation_review", "configuration", "exports"
                ])
            elif user.role == "officer":
                permissions.update([
                    "dashboard", "analytics", "reports", "evidence",
                    "violation_review", "exports"
                ])
            elif user.role == "viewer":
                permissions.update(["dashboard", "analytics"])
                
        return permissions

    def has_permission(self, user: User, permission_name: str) -> bool:
        """Checks if a user holds a specific permission scope."""
        if user.status != "active":
            return False
        user_perms = self.get_user_permissions(user)
        return permission_name in user_perms

    def has_role(self, user: User, role_name: str) -> bool:
        """Checks if user has a particular role assigned."""
        if user.status != "active":
            return False
        # Match from roles relationship first
        for role in user.roles_rel:
            if role.name == role_name:
                return True
        # Fallback to string role column
        return user.role == role_name


# Singleton service instance
rbac_service = RBACService()


# FastAPI Route dependency factory
def require_permission(permission_name: str):
    """
    FastAPI dependency guard protecting routes against unauthorized scopes.
    """
    def dependency(current_user: User = Depends(get_current_user)):
        if not rbac_service.has_permission(current_user, permission_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission scope: {permission_name}"
            )
        return current_user
    return dependency
