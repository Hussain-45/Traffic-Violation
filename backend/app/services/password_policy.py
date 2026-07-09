"""
Password Policy Service
=======================
Validates credential configurations against complexity constraints.
"""
import re


class PasswordPolicyService:
    """
    Enforces secure password strength policies (minimum length, uppercase, digits, symbols).
    """

    def __init__(self):
        self.min_length = 8
        self.require_uppercase = True
        self.require_lowercase = True
        self.require_digit = True
        self.require_special = True

    def validate_password(self, password: str) -> None:
        """
        Validates password complexity. Raises ValueError if validation fails.
        """
        if len(password) < self.min_length:
            raise ValueError(f"Password must be at least {self.min_length} characters long.")

        if self.require_uppercase and not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter.")

        if self.require_lowercase and not re.search(r"[a-z]", password):
            raise ValueError("Password must contain at least one lowercase letter.")

        if self.require_digit and not re.search(r"\d", password):
            raise ValueError("Password must contain at least one numerical digit.")

        if self.require_special and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise ValueError("Password must contain at least one special character.")


# Singleton service instance
password_policy_service = PasswordPolicyService()
