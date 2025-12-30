"""Data source providers for itingen."""

from typing import List, Optional
from itingen.core.base import BaseProvider
from itingen.core.domain.events import Event
from .file_provider import LocalFileProvider

# Alias for backward compatibility or simpler import in CLI
FileProvider = LocalFileProvider

__all__ = ["BaseProvider", "LocalFileProvider", "FileProvider"]
