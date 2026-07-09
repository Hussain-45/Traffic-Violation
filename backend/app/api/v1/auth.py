"""
Authentication & RBAC API endpoints
====================================
Exposes login authentication, refresh token updates, credentials change validation,
and permission maps endpoints.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.auth.jwt import get_current_user
from backend.app.models import User, Role, Permission
from backend.app.schemas.auth_schema import (
    LoginPayload,
    TokenResponse,
    RefreshTokenPayload,
    ChangePasswordPayload,
    UserMeResponse,
    ValidateTokenResponse,
    RoleSchema,
    PermissionSchema
)
from backend.app.controllers.auth_controller import auth_controller

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginPayload,
    request: Request,
    db: Session = Depends(get_db)
):
    """Logs in user, tracks failed login attempts, and returns access/refresh token pair."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    return auth_controller.login(
        db, payload.username, payload.password, payload.remember_me, ip_address, user_agent
    )


@router.post("/logout")
def logout(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Revokes current token session."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Missing authorization header.")
    token = authorization.split(" ")[1]
    success = auth_controller.logout(db, token)
    return {"status": "success", "message": "Logged out successfully."}


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    payload: RefreshTokenPayload,
    request: Request,
    db: Session = Depends(get_db)
):
    """Validates refresh token and generates a new access/refresh pair."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return auth_controller.refresh(db, payload.refresh_token, ip_address, user_agent)


@router.get("/me", response_model=UserMeResponse)
def get_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves current user identity details and list of active permission keys."""
    return auth_controller.get_me(db, current_user)


@router.post("/change-password")
def change_password(
    payload: ChangePasswordPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Updates password hash and revokes other sessions."""
    success = auth_controller.change_password(
        db, current_user, payload.old_password, payload.new_password
    )
    if not success:
        raise HTTPException(status_code=400, detail="Incorrect current password credentials.")
    return {"status": "success", "message": "Password changed successfully."}


@router.post("/validate", response_model=ValidateTokenResponse)
def validate_token(
    payload: Dict[str, str],
    db: Session = Depends(get_db)
):
    """Validates token signatures and sessions without authentication headers."""
    token = payload.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Token payload not provided.")
    return auth_controller.validate_token(token, db)


@router.get("/roles", response_model=List[RoleSchema])
def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists registered role definitions (Admin only permission verification is handled inside route)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Privileged view restricted.")
    return db.query(Role).all()


@router.get("/permissions", response_model=List[PermissionSchema])
def list_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists unique permission keys registered on the platform."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Privileged view restricted.")
    return db.query(Permission).all()
