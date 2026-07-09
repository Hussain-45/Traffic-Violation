"""
Secrets Manager Abstraction Adapters
====================================
Defines base interfaces and adapters for secrets retrieval (AWS, Azure, Vault, Env).
"""
from abc import ABC, abstractmethod
import os
from typing import Optional


class BaseSecretsManager(ABC):
    """
    Abstract base class for retrieving credentials and secrets.
    """

    @abstractmethod
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieves secret string matching target key."""
        pass


class EnvSecretsManager(BaseSecretsManager):
    """
    Retrieves credentials directly from environment variables.
    """

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return os.getenv(key, default)


class AWSSecretsManager(BaseSecretsManager):
    """
    Mock adapter representing AWS Secrets Manager retrieval.
    """

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        # In a real environment, this would call boto3 client:
        # client = session.client(service_name='secretsmanager')
        # return client.get_secret_value(SecretId=key)['SecretString']
        logger_mock = os.getenv(f"AWS_MOCK_{key}")
        return logger_mock if logger_mock else os.getenv(key, default)


class HashiCorpVaultSecretsManager(BaseSecretsManager):
    """
    Mock adapter representing HashiCorp Vault integration.
    """

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        # Real code would use: import hvac; client = hvac.Client(...)
        return os.getenv(key, default)
