"""
Security Context
================
Centralizes user validation, JWT check, blacklist lookup, and active session properties.
"""
from typing import Set, Optional
from pydantic import BaseModel
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import User
from backend.app.services.jwt_service import jwt_service
from backend.app.services.token_blacklist import token_blacklist_service
from backend.app.services.rbac_service import rbac_service


class SecurityContext(BaseModel):
    user: User
    token: str
    session_id: Optional[str] = None
    role: str
    permissions: Set[str]

    class Config:
        arbitrary_types_allowed = True


def get_security_context(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> SecurityContext:
    """
    FastAPI dependency that extracts, verifies, and returns the SecurityContext.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = authorization.split(" ")[1]

    # 1. Check blacklist
    from backend.app.services.token_blacklist import token_blacklist_service
    if token_blacklist_service.is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been revoked. Please log in again."
        )

    # 2. Decode token
    payload = jwt_service.decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired security token."
        )

    username = payload.get("sub")
    session_id = payload.get("session_id")
    
    # 3. Retrieve user
    user = db.query(User).filter(User.username == username).first()
    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user profile."
        )

    # 4. Verify session is not revoked in database
    if session_id:
        from backend.app.models import SessionModel
        session_rec = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session_rec or session_rec.is_revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session revoked."
            )

    permissions = rbac_service.get_user_permissions(user)

    return SecurityContext(
        user=user,
        token=token,
        session_id=session_id,
        role=user.role,
        permissions=permissions
    )


def require_context_permission(permission_name: str):
    """
    FastAPI dependency guard protecting routes using SecurityContext checks.
    """
    def dependency(ctx: SecurityContext = Depends(get_security_context)):
        if permission_name not in ctx.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission scope: {permission_name}"
            )
        return ctx
    return dependency
