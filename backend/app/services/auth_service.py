"""
Authentication Service
======================
Manages user logins, token verification, session tracking, account lockouts,
and permission mapping.
"""
import uuid
import datetime
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models import User, SessionModel, ActivityLog, Role, Permission
from backend.app.services.password_service import password_service
from backend.app.services.jwt_service import jwt_service
from backend.app.services.rbac_service import rbac_service
from backend.app.services.password_policy import password_policy_service
from backend.app.services.token_blacklist import token_blacklist_service
from backend.app.services.identity_adapters import BaseIdentityProvider

LOCKOUT_LIMIT = 5
LOCKOUT_DURATION_MINUTES = 15


class AuthService:
    """
    Coordinates secure user credential operations, session persistence, and security controls.
    """

    def __init__(self):
        self.identity_providers: dict[str, BaseIdentityProvider] = {}

    def register_identity_provider(self, provider_name: str, provider: BaseIdentityProvider):
        """Registers a third-party identity provider adapter."""
        self.identity_providers[provider_name] = provider

    def authenticate_user(
        self, db: Session, username: str, password: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None
    ) -> User:
        """Verifies credentials, handles lockouts, and records activity trails."""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password."
            )

        # 1. Check account lockout status
        if user.locked_until and user.locked_until > datetime.datetime.utcnow():
            remain = int((user.locked_until - datetime.datetime.utcnow()).total_seconds() / 60)
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account locked due to consecutive failures. Try again in {remain} minutes."
            )

        # 2. Check status active
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is deactivated."
            )

        # 3. Verify password
        if not password_service.verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= LOCKOUT_LIMIT:
                user.locked_until = datetime.datetime.utcnow() + datetime.timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                # Audit trail
                db.add(ActivityLog(user_id=user.id, action="Account locked due to too many failed login attempts", ip_address=ip_address))
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail=f"Account locked due to consecutive failures. Try again in {LOCKOUT_DURATION_MINUTES} minutes."
                )
            
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password."
            )

        # 4. Successful login - Reset failed attempts & locked status
        user.failed_login_attempts = 0
        user.locked_until = None
        
        # Log activity
        log = ActivityLog(user_id=user.id, action="User logged in successfully", ip_address=ip_address)
        db.add(log)
        db.commit()

        return user

    def create_user_session(
        self, db: Session, user: User, remember_me: bool = False, ip_address: Optional[str] = None, user_agent: Optional[str] = None
    ) -> SessionModel:
        """Generates refresh session token and persists it to sqlite database."""
        session_id = str(uuid.uuid4())
        
        # Refresh token expiration (remember me prolongs it to 30 days)
        duration_days = 30 if remember_me else 7
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=duration_days)
        
        # Build token signature payload
        payload = {
            "sub": user.username,
            "session_id": session_id,
            "role": user.role
        }
        
        refresh_token = jwt_service.create_refresh_token(payload, datetime.timedelta(days=duration_days))

        session_record = SessionModel(
            id=session_id,
            user_id=user.id,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=expires_at,
            is_revoked=False
        )
        db.add(session_record)
        db.commit()
        db.refresh(session_record)

        return session_record

    def refresh_user_session(
        self, db: Session, refresh_token: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None
    ) -> tuple[str, str]:
        """Validates refresh token payload and issues a new access/refresh pair."""
        payload = jwt_service.decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")

        session_id = payload.get("session_id")
        session_record = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        
        if not session_record or session_record.is_revoked or session_record.expires_at < datetime.datetime.utcnow():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired or revoked session.")

        # Revoke old session and create a new session
        session_record.is_revoked = True
        db.commit()

        user = db.query(User).filter(User.id == session_record.user_id).first()
        if not user or user.status != "active":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user session.")

        # Issue new session record
        new_session = self.create_user_session(db, user, remember_me=False, ip_address=ip_address, user_agent=user_agent)
        
        # Create access token
        access_payload = {
            "sub": user.username,
            "role": user.role,
            "permissions": list(rbac_service.get_user_permissions(user))
        }
        access_token = jwt_service.create_access_token(access_payload)

        return access_token, new_session.refresh_token

    def revoke_session(self, db: Session, token: str) -> bool:
        """Marks active session identifier as revoked to force logout and blacklists JWT."""
        payload = jwt_service.decode_token(token)
        if not payload:
            return False
            
        # Blacklist the JWT token to prevent its reuse
        token_blacklist_service.blacklist_token(token, expires_in_seconds=3600.0)

        session_id = payload.get("session_id")
        if not session_id:
            # Check if it was access token
            username = payload.get("sub")
            # Revoke all sessions for user as fallback or match current active session
            user = db.query(User).filter(User.username == username).first()
            if user:
                db.query(SessionModel).filter(SessionModel.user_id == user.id).update({"is_revoked": True})
                db.commit()
                return True
            return False

        session_record = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if session_record:
            session_record.is_revoked = True
            db.commit()
            return True
        return False

    def change_password(self, db: Session, user: User, old_pass: str, new_pass: str) -> bool:
        """Modifies user credential passwords after verifying current credentials and validating complexity."""
        if not password_service.verify_password(old_pass, user.password_hash):
            return False

        # Validate password complexity via password policy
        password_policy_service.validate_password(new_pass)
            
        user.password_hash = password_service.hash_password(new_pass)
        # Revoke all other active sessions for security compliance
        db.query(SessionModel).filter(SessionModel.user_id == user.id).update({"is_revoked": True})
        db.commit()
        return True


# Singleton service instance
auth_service = AuthService()
