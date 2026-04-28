"""SophonManifest for managing and downloading manifests."""

import asyncio
from collections.abc import AsyncIterator
from typing import Optional

import aiohttp
import zstandard

from .asset import SophonAsset
from .chunk import SophonChunk
from .proto.SophonManifestProto_pb2 import SophonManifestProto
from .speed_limiter import SophonDownloadSpeedLimiter
from .types import (
    SophonChunkManifestInfoPair,
    SophonChunksInfo,
    SophonManifestInfo,
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
        if not info_pair.manifest_info or not info_pair.chunks_info:
            raise ValueError("Invalid manifest info pair")

        manifest_url = info_pair.manifest_info.manifest_file_url
        async with http_client.get(manifest_url) as response:
            response.raise_for_status()
            data = await response.read()

        if info_pair.manifest_info.is_use_compression:
            dctx = zstandard.ZstdDecompressor()
            data = dctx.decompress(data)

        manifest_proto = SophonManifestProto()
        manifest_proto.ParseFromString(data)

        for asset_prop in manifest_proto.Assets:
            asset = SophonAsset(
                asset_name=asset_prop.AssetName,
                asset_size=asset_prop.AssetSize,
                asset_hash=asset_prop.AssetHashMd5,
                is_directory=(asset_prop.AssetSize == 0 and not asset_prop.AssetChunks),
                sophon_chunks_info=info_pair.chunks_info,
                download_speed_limiter=download_speed_limiter
            )

            for chunk_prop in asset_prop.AssetChunks:
                chunk = SophonChunk(
                    chunk_name=chunk_prop.ChunkName,
                    chunk_hash_decompressed=bytes.fromhex(chunk_prop.ChunkDecompressedHashMd5),
                    chunk_offset=chunk_prop.ChunkOnFileOffset,
                    chunk_size=chunk_prop.ChunkSize,
                    chunk_size_decompressed=chunk_prop.ChunkSizeDecompressed
                )
                asset.chunks.append(chunk)

            yield asset

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
        try:
            async with client.get(url) as response:
                response.raise_for_status()
                json_data = await response.json()
        except Exception as e:
            if is_throw_if_not_found:
                raise ValueError(f"Failed to fetch manifest pair: {e}") from e
            return SophonChunkManifestInfoPair(is_found=False, return_message=str(e))

        if not isinstance(json_data, dict):
            if is_throw_if_not_found:
                raise ValueError(f"Invalid API response: Expected dict, got {type(json_data).__name__}")
            return SophonChunkManifestInfoPair(is_found=False, return_message="Invalid API response")

        if "retcode" not in json_data:
            if is_throw_if_not_found:
                raise ValueError("Invalid API response: Missing 'retcode' field")
            return SophonChunkManifestInfoPair(is_found=False, return_message="Missing retcode")

        if json_data["retcode"] != 0:
            error_msg = json_data.get("message", "Unknown API error")
            if is_throw_if_not_found:
                raise ValueError(f"API error ({json_data['retcode']}): {error_msg}")
            return SophonChunkManifestInfoPair(is_found=False, return_message=f"API error: {error_msg}")

        if "data" not in json_data or not isinstance(json_data["data"], dict):
            if is_throw_if_not_found:
                raise ValueError("Invalid API response: Missing or invalid 'data' field")
            return SophonChunkManifestInfoPair(is_found=False, return_message="Missing data field")

        data = json_data["data"]
        if "manifests" not in data or not isinstance(data["manifests"], list):
            if is_throw_if_not_found:
                raise ValueError("Invalid API response: Missing or invalid 'manifests' field")
            return SophonChunkManifestInfoPair(is_found=False, return_message="Missing manifests field")

        manifests = data["manifests"]

        target_manifest = None
        for m in manifests:
            if m.get("matching_field") == matching_field:
                target_manifest = m
                break

        if not target_manifest:
            if is_throw_if_not_found:
                raise ValueError(f"Manifest with matching_field '{matching_field}' not found")
            return SophonChunkManifestInfoPair(is_found=False, return_message="Not found")

        manifest_data = target_manifest.get("manifest", {})
        md = target_manifest.get("manifest_download", {})
        cd = target_manifest.get("chunk_download", {})
        stats = target_manifest.get("stats", {})

        manifest_info = SophonManifest.create_manifest_info(
            manifest_base_url=md.get("url_prefix", ""),
            manifest_checksum_md5=manifest_data.get("checksum", ""),
            manifest_id=manifest_data.get("id", ""),
            is_use_compression=md.get("compression", 0) == 1,
            manifest_size=int(manifest_data.get("uncompressed_size", 0) or 0),
            manifest_compressed_size=int(manifest_data.get("compressed_size", 0) or 0),
            matching_field=matching_field,
        )

        chunks_info = SophonManifest.create_chunks_info(
            chunks_base_url=cd.get("url_prefix", ""),
            chunks_count=int(stats.get("chunk_count", 0) or 0),
            files_count=int(stats.get("file_count", 0) or 0),
            is_use_compression=cd.get("compression", 0) == 1,
            total_size=int(stats.get("uncompressed_size", 0) or 0),
            total_compressed_size=int(stats.get("compressed_size", 0) or 0),
            matching_field=matching_field,
        )

        return SophonChunkManifestInfoPair(
            chunks_info=chunks_info,
            manifest_info=manifest_info,
            is_found=True
        )

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
