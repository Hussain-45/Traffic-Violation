"""
Storage Service Abstraction
===========================
Defines the StorageAdapter interface and a LocalFileSystem adapter implementation.
Enables swapping local directories with AWS S3 or Azure Blob storage seamlessly.
"""
import os
from abc import ABC, abstractmethod


class StorageAdapter(ABC):
    """
    Abstract interface defining storage read/write contracts.
    """

    @abstractmethod
    def save(self, file_path: str, data: bytes) -> str:
        """Saves binary data to storage and returns access URI/filepath."""
        pass

    @abstractmethod
    def get(self, file_path: str) -> bytes:
        """Retrieves binary data from storage."""
        pass

    @abstractmethod
    def delete(self, file_path: str) -> bool:
        """Deletes file from storage."""
        pass

    @abstractmethod
    def exists(self, file_path: str) -> bool:
        """Checks if file exists in storage."""
        pass


class LocalStorageAdapter(StorageAdapter):
    """
    Local filesystem implementation of StorageAdapter.
    """

    def __init__(self, base_dir: str = "data"):
        self.base_dir = base_dir

    def _get_absolute_path(self, file_path: str) -> str:
        # Strip leading slashes to prevent absolute path breaking base_dir join
        cleaned_path = file_path.lstrip("/").lstrip("\\")
        return os.path.join(self.base_dir, cleaned_path)

    def save(self, file_path: str, data: bytes) -> str:
        abs_path = self._get_absolute_path(file_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        
        mode = "wb"
        with open(abs_path, mode) as f:
            f.write(data)
        return file_path

    def get(self, file_path: str) -> bytes:
        abs_path = self._get_absolute_path(file_path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"File not found in local storage: {file_path}")
            
        with open(abs_path, "rb") as f:
            return f.read()

    def delete(self, file_path: str) -> bool:
        abs_path = self._get_absolute_path(file_path)
        if os.path.exists(abs_path):
            try:
                os.remove(abs_path)
                return True
            except Exception:
                return False
        return False

    def exists(self, file_path: str) -> bool:
        abs_path = self._get_absolute_path(file_path)
        return os.path.exists(abs_path)


# Singleton local storage adapter instance
storage_service = LocalStorageAdapter()
