"""
Token Blacklist Service
======================
Manages in-memory revoked JWT tokens, prepared for Redis cache swap.
"""
import time
from typing import Dict


class TokenBlacklistService:
    """
    Tracks tokens marked as revoked/logged out before their natural JWT expiration.
    """

    def __init__(self):
        # Maps token string to expiration epoch timestamp (so we can sweep expired items)
        self._blacklist: Dict[str, float] = {}

    def blacklist_token(self, token: str, expires_in_seconds: float = 3600.0) -> None:
        """Adds token to blacklist with an expiration timeline."""
        expiry_time = time.time() + expires_in_seconds
        self._blacklist[token] = expiry_time
        self._clean_expired()

    def is_token_blacklisted(self, token: str) -> bool:
        """Verifies if token has been revoked."""
        self._clean_expired()
        return token in self._blacklist

    def _clean_expired(self) -> None:
        """Sweeps expired tokens from memory periodically."""
        now = time.time()
        expired_tokens = [t for t, exp in self._blacklist.items() if exp < now]
        for t in expired_tokens:
            self._blacklist.pop(t, None)


# Singleton service instance
token_blacklist_service = TokenBlacklistService()
