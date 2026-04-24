"""SophonManifest for managing and downloading manifests."""

from typing import AsyncIterator, Optional
import asyncio
import aiohttp

from .asset import SophonAsset
from .speed_limiter import SophonDownloadSpeedLimiter
from .types import (
    SophonChunkManifestInfoPair,
    SophonManifestInfo,
    SophonChunksInfo,
)


class SophonManifest:
    """Manifest management for Sophon protocol."""

    @staticmethod
    async def enumerate_async(
        http_client: aiohttp.ClientSession,
        info_pair: SophonChunkManifestInfoPair,
        download_speed_limiter: Optional[SophonDownloadSpeedLimiter] = None,
        token: Optional[asyncio.CancelledError] = None,
    ) -> AsyncIterator[SophonAsset]:
        """
        Enumerate assets from manifest.

        Args:
            http_client: aiohttp ClientSession.
            info_pair: Manifest and chunks info pair.
            download_speed_limiter: Optional speed limiter.
            token: Cancellation token.

        Yields:
            SophonAsset: Assets from the manifest.

        Raises:
            ValueError: If manifest info is invalid.
            aiohttp.ClientError: If HTTP request fails.
        """
        # TODO: Implement manifest enumeration
        yield  # Placeholder to make this an async generator

    @staticmethod
    async def create_chunk_manifest_info_pair(
        client: aiohttp.ClientSession,
        url: str,
        matching_field: str = "game",
        is_throw_if_not_found: bool = True,
        token: Optional[asyncio.CancelledError] = None,
    ) -> SophonChunkManifestInfoPair:
        """
        Create manifest info pair from branch API.

        Args:
            client: aiohttp ClientSession.
            url: Branch API URL.
            matching_field: Matching field name (usually "game").
            is_throw_if_not_found: Raise exception if not found.
            token: Cancellation token.

        Returns:
            SophonChunkManifestInfoPair: Created info pair.

        Raises:
            ValueError: If URL is invalid or manifest not found.
            aiohttp.ClientError: If HTTP request fails.
        """
        # TODO: Implement branch API parsing
        pass

    @staticmethod
    def create_manifest_info(
        manifest_base_url: str,
        manifest_checksum_md5: str,
        manifest_id: str,
        is_use_compression: bool,
        manifest_size: int,
        manifest_compressed_size: int,
        matching_field: Optional[str] = None,
        category_id: int = 0,
        category_name: Optional[str] = None,
    ) -> SophonManifestInfo:
        """
        Create manifest info object.

        Args:
            manifest_base_url: Base URL for manifest.
            manifest_checksum_md5: MD5 checksum of manifest.
            manifest_id: Manifest ID/filename.
            is_use_compression: Whether manifest is compressed.
            manifest_size: Uncompressed size of manifest.
            manifest_compressed_size: Compressed size of manifest.
            matching_field: Matching field for categorization.
            category_id: Category ID.
            category_name: Category name.

        Returns:
            SophonManifestInfo: Created manifest info object.
        """
        info = SophonManifestInfo(
            manifest_base_url=manifest_base_url,
            manifest_checksum_md5=manifest_checksum_md5,
            manifest_id=manifest_id,
            is_use_compression=is_use_compression,
            manifest_size=manifest_size,
            manifest_compressed_size=manifest_compressed_size,
            matching_field=matching_field,
            category_id=category_id,
            category_name=category_name,
        )
        return info

    @staticmethod
    def create_chunks_info(
        chunks_base_url: str,
        chunks_count: int,
        files_count: int,
        is_use_compression: bool,
        total_size: int,
        total_compressed_size: int,
        matching_field: Optional[str] = None,
        category_id: int = 0,
        category_name: Optional[str] = None,
    ) -> SophonChunksInfo:
        """
        Create chunks info object.

        Args:
            chunks_base_url: Base URL for chunks.
            chunks_count: Number of chunks.
            files_count: Number of files.
            is_use_compression: Whether chunks are compressed.
            total_size: Total uncompressed size.
            total_compressed_size: Total compressed size.
            matching_field: Matching field for categorization.
            category_id: Category ID.
            category_name: Category name.

        Returns:
            SophonChunksInfo: Created chunks info object.
        """
        info = SophonChunksInfo(
            chunks_base_url=chunks_base_url,
            chunks_count=chunks_count,
            files_count=files_count,
            is_use_compression=is_use_compression,
            total_size=total_size,
            total_compressed_size=total_compressed_size,
            matching_field=matching_field,
            category_id=category_id,
            category_name=category_name,
        )
        return info
