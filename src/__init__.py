"""
iiko API SDK - Python клиент для работы с API iiko.
"""

__version__ = "0.1.0"

from .iiko_sdk import IikoSDK
from .config import Settings, get_settings
from .auth import AuthManager
from .client import HTTPClient

__all__ = [
    "IikoSDK",
    "Settings",
    "get_settings",
    "AuthManager",
    "HTTPClient",
]
