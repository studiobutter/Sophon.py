"""SophonUpdate for handling game updates."""

import asyncio
from collections.abc import AsyncIterator
from typing import Optional

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
        from .manifest import SophonManifest

        # Build map of old assets
        old_assets = {}
        async for old_asset in SophonManifest.enumerate_async(
            http_client, info_pair_old, download_speed_limiter, token
        ):
            old_assets[old_asset.asset_name] = old_asset

        # Enumerate new assets and find changes
        async for new_asset in SophonManifest.enumerate_async(
            http_client, info_pair_new, download_speed_limiter, token
        ):
            existing_asset = old_assets.get(new_asset.asset_name)

            if not existing_asset:
                # Completely new asset
                new_asset.is_has_patch = False
                yield new_asset
                continue

            if new_asset.asset_hash == existing_asset.asset_hash:
                # No changes
                continue

            # Asset has changed, link old chunks for diff update
            new_asset.is_has_patch = True

            # For a proper update, we want chunks to point to old chunk offsets where hash matches
            # Wait, in the Sophon protocol, chunks that match decompressed hash can be copied
            # from the old file directly. Let's map old chunk hashes to their offsets
            old_chunks_by_hash = {
                c.chunk_hash_decompressed: c
                for c in old_asset.chunks
            }

            for chunk in new_asset.chunks:
                if chunk.chunk_hash_decompressed in old_chunks_by_hash:
                    old_chunk = old_chunks_by_hash[chunk.chunk_hash_decompressed]
                    chunk.chunk_old_offset = old_chunk.chunk_offset

            yield new_asset
