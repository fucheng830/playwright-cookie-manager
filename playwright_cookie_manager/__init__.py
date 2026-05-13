"""Playwright Cookie Manager — universal browser cookie storage."""
from .manager import CookieManager
from .types import CookieAccount, CookieData
from .backends.file import FileBackend

__version__ = "0.1.0"
__all__ = ["CookieManager", "CookieAccount", "CookieData", "FileBackend"]
