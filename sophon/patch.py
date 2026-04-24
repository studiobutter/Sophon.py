"""SophonPatch for handling game patches and updates using HDiffPatch."""

from dataclasses import dataclass, field
from typing import Optional, Callable, List, AsyncIterator
from enum import Enum
import asyncio
import aiohttp

from .chunk import SophonChunk
from .speed_limiter import SophonDownloadSpeedLimiter
from .types import (
    IdentifiableProperty,
    SophonChunksInfo,
    SophonChunkManifestInfoPair,
)


class SophonPatchMethod(Enum):
    """Method for applying patches."""

    COPY_OVER = "CopyOver"
    DOWNLOAD_OVER = "DownloadOver"
    PATCH = "Patch"
    REMOVE = "Remove"


@dataclass
class SophonPatchAsset(IdentifiableProperty):
    """Represents a patch asset for updating files."""

    main_asset_info: Optional["SophonAsset"] = None
    patch_info: Optional[SophonChunksInfo] = None
    patch_method: SophonPatchMethod = SophonPatchMethod.PATCH
    patch_name_source: str = ""
    patch_hash: str = ""
    patch_offset: int = 0
    patch_size: int = 0
    patch_chunk_length: int = 0
    original_file_path: str = ""
    original_file_hash: str = ""
    original_file_size: int = 0
    target_file_path: str = ""
    target_file_hash: str = ""
    target_file_size: int = 0

    async def download_patch_async(
        self,
        client: aiohttp.ClientSession,
        input_dir: str,
        patch_output_dir: str,
        force_verification: bool = False,
        download_read_delegate: Optional[Callable[[int], None]] = None,
        download_speed_limiter: Optional[SophonDownloadSpeedLimiter] = None,
        token: Optional[asyncio.CancelledError] = None,
    ) -> bool:
        """
        Download patch file.

        Args:
            client: aiohttp ClientSession.
            input_dir: Input directory.
            patch_output_dir: Output directory for patch.
            force_verification: Force verification of patch.
            download_read_delegate: Callback for download progress.
            download_speed_limiter: Optional speed limiter.
            token: Cancellation token.

        Returns:
            bool: True if successful, False otherwise.

        Raises:
            aiohttp.ClientError: If download fails.
            IOError: If file operations fail.
        """
        # TODO: Implement patch download logic
        return True

    async def apply_patch_update_async(
        self,
        client: aiohttp.ClientSession,
        input_dir: str,
        patch_output_dir: str,
        remove_old_assets: bool = True,
        download_read_delegate: Optional[Callable[[int], None]] = None,
        disk_write_delegate: Optional[Callable[[int], None]] = None,
        download_speed_limiter: Optional[SophonDownloadSpeedLimiter] = None,
        token: Optional[asyncio.CancelledError] = None,
    ) -> None:
        """
        Apply patch to update file.

        Args:
            client: aiohttp ClientSession.
            input_dir: Input directory with old files.
            patch_output_dir: Directory with patch files.
            remove_old_assets: Remove old assets after patching.
            download_read_delegate: Callback for download progress.
            disk_write_delegate: Callback for disk write progress.
            download_speed_limiter: Optional speed limiter.
            token: Cancellation token.

        Raises:
            aiohttp.ClientError: If download fails.
            IOError: If file operations fail.
        """
        # TODO: Implement patch application logic
        pass

    def __str__(self) -> str:
        """Return target file path as string representation."""
        return self.target_file_path


class SophonPatch:
    """Patch management for Sophon protocol."""

    @staticmethod
    async def enumerate_update_async(
        http_client: aiohttp.ClientSession,
        patch_info_pair: Optional[SophonChunkManifestInfoPair],
        main_info_pair: SophonChunkManifestInfoPair,
        version_tag_update_from: str,
        download_speed_limiter: Optional[SophonDownloadSpeedLimiter] = None,
        token: Optional[asyncio.CancelledError] = None,
    ) -> AsyncIterator[SophonPatchAsset]:
        """
        Enumerate patch assets for updating from specific version.

        Args:
            http_client: aiohttp ClientSession.
            patch_info_pair: Patch manifest info pair (optional).
            main_info_pair: Main manifest info pair.
            version_tag_update_from: Version to update from.
            download_speed_limiter: Optional speed limiter.
            token: Cancellation token.

        Yields:
            SophonPatchAsset: Patch assets to apply.

        Raises:
            ValueError: If version tag not found.
            aiohttp.ClientError: If HTTP request fails.
        """
        # TODO: Implement patch enumeration logic
        yield  # Placeholder to make this an async generator

    @staticmethod
    async def create_chunk_manifest_info_pair(
        client: aiohttp.ClientSession,
        url: str,
        version_tag_update_from: str,
        matching_field: Optional[str] = None,
        token: Optional[asyncio.CancelledError] = None,
    ) -> SophonChunkManifestInfoPair:
        """
        Create patch manifest info pair from API.

        Args:
            client: aiohttp ClientSession.
            url: Patch API URL.
            version_tag_update_from: Version tag to update from.
            matching_field: Matching field name (usually "game").
            token: Cancellation token.

        Returns:
            SophonChunkManifestInfoPair: Created patch info pair.

        Raises:
            ValueError: If URL or version invalid.
            aiohttp.ClientError: If HTTP request fails.
        """
        # TODO: Implement patch branch API parsing
        pass
