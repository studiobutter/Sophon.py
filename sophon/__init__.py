"""
Sophon - A Python library for downloading HoYoverse games using the Sophon protocol.

This is a port of Hi3Helper.Sophon to Python with async/await support.
"""

__version__ = "0.1.0"
__author__ = "Sophon.py Contributors"
__license__ = "MIT"

from .asset import SophonAsset
from .manifest import SophonManifest
from .update import SophonUpdate
from .patch import SophonPatch, SophonPatchAsset
from .speed_limiter import SophonDownloadSpeedLimiter
from .exceptions import (
    SophonException,
    ManifestNotFoundError,
    ChunkVerificationError,
    DownloadError,
)

__all__ = [
    "SophonAsset",
    "SophonManifest",
    "SophonUpdate",
    "SophonPatch",
    "SophonPatchAsset",
    "SophonDownloadSpeedLimiter",
    "SophonException",
    "ManifestNotFoundError",
    "ChunkVerificationError",
    "DownloadError",
]
