"""
Identity Provider Adapters
==========================
Defines abstraction interfaces for third-party identity providers (OAuth2, LDAP, SAML).
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseIdentityProvider(ABC):
    """
    Abstract adapter for integration with third-party Identity Providers.
    """

    @abstractmethod
    def authenticate(self, credentials: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Authenticates a user against the IdP.
        Returns a dict of user profile information if successful, otherwise None.
        """
        pass


class OAuth2GoogleAdapter(BaseIdentityProvider):
    """
    Mock adapter representing Google OAuth2 sign-in.
    """

    def authenticate(self, credentials: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        token = credentials.get("id_token")
        if not token:
            return None
        # Mock Google validation logic
        if token == "mock-google-token":
            return {
                "username": "google_user",
                "email": "user@gmail.com",
                "full_name": "Google User",
                "provider": "google"
            }
        return None


class LDAPAdapter(BaseIdentityProvider):
    """
    Mock adapter representing LDAP/Active Directory login.
    """

    def authenticate(self, credentials: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        username = credentials.get("username")
        password = credentials.get("password")
        if not username or not password:
            return None
        # Mock LDAP lookup logic
        if username.endswith("@corp.local") and password == "CorpPass123":
            return {
                "username": username.split("@")[0],
                "email": username,
                "full_name": "Active Directory User",
                "provider": "ldap"
            }
        return None
