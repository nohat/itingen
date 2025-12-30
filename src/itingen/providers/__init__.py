"""Data source providers for itingen."""

from itingen.core.base import BaseProvider
from .file_provider import LocalFileProvider

# Alias for backward compatibility or simpler import in CLI
FileProvider = LocalFileProvider

__all__ = ["BaseProvider", "LocalFileProvider", "FileProvider"]
