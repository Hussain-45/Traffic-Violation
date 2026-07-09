"""
Auth Controller
===============
Mediates HTTP endpoints to authentication services and maps schemas.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.services.auth_service import auth_service
from backend.app.services.jwt_service import jwt_service
from backend.app.services.rbac_service import rbac_service
from backend.app.models import User
from backend.app.schemas.auth_schema import TokenResponse, UserMeResponse, ValidateTokenResponse


class AuthController:
    """
    Mediator between FastAPI auth router endpoints and security services.
    """

    def login(
        self, db: Session, username: str, password: str, remember_me: bool, ip_address: Optional[str], user_agent: Optional[str]
    ) -> TokenResponse:
        user = auth_service.authenticate_user(db, username, password, ip_address, user_agent)
        session = auth_service.create_user_session(db, user, remember_me, ip_address, user_agent)
        
        # Access token payload contains permissions
        access_payload = {
            "sub": user.username,
            "session_id": session.id,
            "role": user.role,
            "permissions": list(rbac_service.get_user_permissions(user))
        }
        access_token = jwt_service.create_access_token(access_payload)

        return TokenResponse(
            access_token=access_token,
            refresh_token=session.refresh_token,
            token_type="bearer"
        )

    def logout(self, db: Session, token: str) -> bool:
        return auth_service.revoke_session(db, token)

    def refresh(
        self, db: Session, refresh_token: str, ip_address: Optional[str], user_agent: Optional[str]
    ) -> TokenResponse:
        access_token, new_refresh_token = auth_service.refresh_user_session(
            db, refresh_token, ip_address, user_agent
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )

    def get_me(self, db: Session, user: User) -> UserMeResponse:
        permissions = list(rbac_service.get_user_permissions(user))
        return UserMeResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            status=user.status,
            permissions=permissions
        )

    def change_password(self, db: Session, user: User, old_pass: str, new_pass: str) -> bool:
        return auth_service.change_password(db, user, old_pass, new_pass)

    def validate_token(self, token: str, db: Session) -> ValidateTokenResponse:
        payload = jwt_service.decode_token(token)
        if not payload:
            return ValidateTokenResponse(valid=False)

        username = payload.get("sub")
        role = payload.get("role")
        permissions = payload.get("permissions", [])

        # Verify user still exists and is active
        from backend.app.models import User
        user = db.query(User).filter(User.username == username).first()
        if not user or user.status != "active":
            return ValidateTokenResponse(valid=False)

        # Verify session is not revoked if session_id is in token
        session_id = payload.get("session_id")
        if session_id:
            from backend.app.models import SessionModel
            session_rec = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if not session_rec or session_rec.is_revoked:
                return ValidateTokenResponse(valid=False)

        return ValidateTokenResponse(
            valid=True,
            user_id=user.id,
            username=username,
            role=role,
            permissions=permissions
        )


# Singleton controller instance
auth_controller = AuthController()
