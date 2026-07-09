"""
Password Service
================
Provides standard password hashing and verification wraps via bcrypt.
"""
import bcrypt


class PasswordService:
    """
    Handles cryptographic verification and generation of user credentials.
    """

    def hash_password(self, password: str) -> str:
        """Generates a secure bcrypt password hash."""
        pw_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifies a plain text password against a bcrypt hash."""
        try:
            pw_bytes = plain_password.encode("utf-8")
            hash_bytes = hashed_password.encode("utf-8") if isinstance(hashed_password, str) else hashed_password
            return bcrypt.checkpw(pw_bytes, hash_bytes)
        except Exception:
            return False


# Singleton service instance
password_service = PasswordService()
