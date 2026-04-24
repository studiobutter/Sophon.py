"""SophonUpdate for handling game updates."""

from typing import AsyncIterator, Optional
import asyncio
import aiohttp

from .asset import SophonAsset
from .speed_limiter import SophonDownloadSpeedLimiter
from .types import SophonChunkManifestInfoPair


class SophonUpdate:
    """Update management for Sophon protocol."""

    @staticmethod
    async def enumerate_update_async(
        http_client: aiohttp.ClientSession,
        info_pair_old: SophonChunkManifestInfoPair,
        info_pair_new: SophonChunkManifestInfoPair,
        remove_chunk_after_apply: bool = False,
        download_speed_limiter: Optional[SophonDownloadSpeedLimiter] = None,
        token: Optional[asyncio.CancelledError] = None,
    ) -> AsyncIterator[SophonAsset]:
        """
        Enumerate changed assets between old and new manifest.

        Compares two manifests and yields only the assets that have changed,
        allowing efficient incremental updates.

        Args:
            http_client: aiohttp ClientSession.
            info_pair_old: Old manifest and chunks info pair.
            info_pair_new: New manifest and chunks info pair.
            remove_chunk_after_apply: Remove chunks after applying.
            download_speed_limiter: Optional speed limiter.
            token: Cancellation token.

        Yields:
            SophonAsset: Changed assets from old to new.

        Raises:
            ValueError: If manifest info is invalid.
            aiohttp.ClientError: If HTTP request fails.
        """
        # TODO: Implement update enumeration logic
        yield  # Placeholder to make this an async generator
