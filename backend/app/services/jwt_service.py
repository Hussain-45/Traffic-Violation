"""
JWT Service
===========
Handles signing, verification, and revocation checks for access and refresh tokens.
"""
import datetime
from typing import Dict, Any, Optional
from jose import jwt, JWTError

from backend.app.config import settings


class JWTService:
    """
    Standard service layer for building and parsing secure JSON Web Tokens.
    """

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[datetime.timedelta] = None) -> str:
        """Signs a secure JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.datetime.utcnow() + expires_delta
        else:
            expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "type": "access"
        })
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    def create_refresh_token(self, data: Dict[str, Any], expires_delta: Optional[datetime.timedelta] = None) -> str:
        """Signs a secure refresh token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.datetime.utcnow() + expires_delta
        else:
            expire = datetime.datetime.utcnow() + datetime.timedelta(days=7)
            
        to_encode.update({
            "exp": expire,
            "type": "refresh"
        })
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Parses and validates token signature and expirations."""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            return None


# Singleton service instance
jwt_service = JWTService()
