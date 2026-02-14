"""Data source providers for itingen."""

from itingen.core.base import BaseProvider
from .file_provider import LocalFileProvider
from .database_provider import DatabaseProvider

# Alias for backward compatibility or simpler import in CLI
FileProvider = LocalFileProvider

__all__ = ["BaseProvider", "LocalFileProvider", "FileProvider", "DatabaseProvider"]
