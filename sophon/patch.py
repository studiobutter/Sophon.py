"""SophonPatch for handling game patches and updates using HDiffPatch."""

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    from .asset import SophonAsset

import aiohttp

from .speed_limiter import SophonDownloadSpeedLimiter
from .types import (
    IdentifiableProperty,
    SophonChunkManifestInfoPair,
    SophonChunksInfo,
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
        import logging
        import os

        from .asset import SophonAsset, SourceStreamType
        from .chunk import SophonChunk

        logger = logging.getLogger(__name__)

        if self.patch_method in (SophonPatchMethod.REMOVE, SophonPatchMethod.DOWNLOAD_OVER):
            return True

        if token is None:
            token = asyncio.CancelledError()

        patch_hash_bytes = bytes.fromhex(self.patch_hash) if len(self.patch_hash) == 32 else self.patch_hash.encode()

        patch_chunk = SophonChunk(
            chunk_name=self.patch_name_source,
            chunk_hash_decompressed=patch_hash_bytes,
            chunk_offset=0,
            chunk_old_offset=0,
            chunk_size=self.patch_size,
            chunk_size_decompressed=self.patch_size,
            is_skip_hash_check_on_write=True
        )

        os.makedirs(patch_output_dir, exist_ok=True)
        patch_file_path = os.path.join(patch_output_dir, self.patch_name_source)

        is_patch_matched = False
        if os.path.exists(patch_file_path):
            file_size = os.path.getsize(patch_file_path)
            is_patch_matched = file_size == self.patch_size

            if is_patch_matched and force_verification:
                with open(patch_file_path, "rb") as f:
                    is_patch_matched = await patch_chunk.check_chunk_hash_async(f, True)

        if is_patch_matched:
            if download_read_delegate:
                download_read_delegate(self.patch_size)
            return True

        logger.debug(f"Downloading patch {self.patch_name_source} to {patch_file_path}")

        temp_asset = SophonAsset(
            asset_name=self.patch_name_source,
            asset_size=self.patch_size,
            chunks=[patch_chunk],
            sophon_chunks_info=self.patch_info,
            download_speed_limiter=download_speed_limiter
        )

        temp_patch_file_path = f"{patch_file_path}.tmp"

        try:
            with open(temp_patch_file_path, "wb"):
                pass

            def download_info_wrapper(read_bytes: int, net_bytes: int):
                if download_read_delegate:
                    download_read_delegate(net_bytes)

            with open(temp_patch_file_path, "r+b") as stream:
                await temp_asset._inner_write_stream_to_async(
                    client=client,
                    source_stream=None,
                    source_stream_type=SourceStreamType.INTERNET,
                    out_stream=stream,
                    chunk=patch_chunk,
                    write_info_delegate=None,
                    download_info_delegate=download_info_wrapper,
                    token=token
                )

            os.replace(temp_patch_file_path, patch_file_path)
            return True
        except asyncio.CancelledError:
            if os.path.exists(temp_patch_file_path):
                try:
                    os.remove(temp_patch_file_path)
                except OSError:
                    pass
            raise
        except Exception as e:
            logger.error(f"Failed to download patch chunk {self.patch_name_source}: {e}")
            if os.path.exists(temp_patch_file_path):
                try:
                    os.remove(temp_patch_file_path)
                except OSError:
                    pass
            raise

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
        import logging
        import os
        import shutil

        logger = logging.getLogger(__name__)

        if token is None:
            token = asyncio.CancelledError()

        base_input_dir = os.path.abspath(input_dir)
        base_patch_dir = os.path.abspath(patch_output_dir)

        def _get_safe_path(base_dir, file_path):
            full_path = os.path.abspath(os.path.join(base_dir, file_path))
            if not full_path.startswith(base_dir):
                raise ValueError(f"Path traversal attempt detected: {file_path}")
            return full_path

        class IPatchStrategy:
            async def apply(self) -> None:
                raise NotImplementedError

        class RemovePatchStrategy(IPatchStrategy):
            async def apply(self) -> None:
                if not remove_old_assets:
                    return
                original_path = _get_safe_path(base_input_dir, self_asset.original_file_path)
                if os.path.exists(original_path):
                    try:
                        os.remove(original_path)
                        logger.debug(f"Removed old asset: {original_path}")
                    except Exception as e:
                        logger.error(f"Failed to delete old asset {original_path}: {e}")

        class DownloadOverPatchStrategy(IPatchStrategy):
            async def apply(self) -> None:
                target_path = _get_safe_path(base_input_dir, self_asset.target_file_path)
                temp_target_path = f"{target_path}.temp"
                os.makedirs(os.path.dirname(target_path) or ".", exist_ok=True)

                try:
                    if self_asset.main_asset_info:
                        self_asset.main_asset_info.download_speed_limiter = download_speed_limiter
                        await self_asset.main_asset_info.write_to_stream_async(
                            client=client,
                            output_path=temp_target_path,
                            write_info_delegate=disk_write_delegate,
                            download_info_delegate=lambda x, y: download_read_delegate(x) if download_read_delegate else None,
                            token=token
                        )

                    if os.path.exists(target_path):
                        os.remove(target_path)
                    shutil.move(temp_target_path, target_path)
                except Exception as e:
                    logger.error(f"Failed DownloadOver for {self_asset.target_file_path}: {e}")
                    if os.path.exists(temp_target_path):
                        os.remove(temp_target_path)
                    raise

        class CopyOverPatchStrategy(IPatchStrategy):
            async def apply(self) -> None:
                target_path = _get_safe_path(base_input_dir, self_asset.target_file_path)
                temp_target_path = f"{target_path}.temp"
                patch_file = _get_safe_path(base_patch_dir, self_asset.patch_name_source)
                os.makedirs(os.path.dirname(target_path) or ".", exist_ok=True)

                try:
                    with open(patch_file, "rb") as src, open(temp_target_path, "wb") as dst:
                        src.seek(self_asset.patch_offset)
                        remaining = self_asset.patch_chunk_length
                        buffer_size = 512 * 1024

                        while remaining > 0:
                            to_read = min(buffer_size, remaining)
                            data = src.read(to_read)
                            if not data:
                                break
                            dst.write(data)
                            remaining -= len(data)
                            if disk_write_delegate:
                                disk_write_delegate(len(data))

                    if os.path.exists(target_path):
                        os.remove(target_path)
                    shutil.move(temp_target_path, target_path)
                except Exception as e:
                    logger.error(f"Failed CopyOver for {self_asset.target_file_path}: {e}")
                    if os.path.exists(temp_target_path):
                        os.remove(temp_target_path)
                    raise

        class BinaryDiffPatchStrategy(IPatchStrategy):
            async def apply(self) -> None:
                target_path = _get_safe_path(base_input_dir, self_asset.target_file_path)
                temp_target_path = f"{target_path}.temp"
                original_path = _get_safe_path(base_input_dir, self_asset.original_file_path)
                patch_file = _get_safe_path(base_patch_dir, self_asset.patch_name_source)
                os.makedirs(os.path.dirname(target_path) or ".", exist_ok=True)

                hpatchz_path = os.environ.get("HPATCHZ_PATH", "hpatchz")

                try:
                    cmd = [
                        hpatchz_path,
                        "-f",
                        original_path,
                        patch_file,
                        temp_target_path
                    ]

                    logger.debug(f"Running hpatchz: {' '.join(cmd)}")

                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )

                    stdout, stderr = await process.communicate()

                    if process.returncode != 0:
                        error_msg = stderr.decode() or stdout.decode()
                        raise RuntimeError(f"hpatchz failed with exit code {process.returncode}: {error_msg}")

                    if disk_write_delegate:
                        disk_write_delegate(self_asset.target_file_size)

                    if os.path.exists(target_path):
                        os.remove(target_path)
                    shutil.move(temp_target_path, target_path)

                    if original_path.endswith(".diff_ref") or remove_old_assets:
                        if os.path.exists(original_path) and original_path != target_path:
                            try:
                                os.remove(original_path)
                            except OSError:
                                pass

                except asyncio.CancelledError:
                    raise
                except OSError as e:
                    logger.error(f"Failed HDiffPatch OS Error for {self_asset.target_file_path}: {e}")
                    if os.path.exists(temp_target_path):
                        try:
                            os.remove(temp_target_path)
                        except OSError:
                            pass
                    raise
                except RuntimeError as e:
                    logger.error(f"Failed HDiffPatch Runtime Error for {self_asset.target_file_path}: {e}")
                    if os.path.exists(temp_target_path):
                        try:
                            os.remove(temp_target_path)
                        except OSError:
                            pass
                    raise

        self_asset = self
        strategies = {
            SophonPatchMethod.REMOVE: RemovePatchStrategy(),
            SophonPatchMethod.DOWNLOAD_OVER: DownloadOverPatchStrategy(),
            SophonPatchMethod.COPY_OVER: CopyOverPatchStrategy(),
            SophonPatchMethod.PATCH: BinaryDiffPatchStrategy(),
        }

        strategy = strategies.get(self.patch_method)
        if not strategy:
            raise ValueError(f"Unknown patch method: {self.patch_method}")

        await strategy.apply()

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
        if not patch_info_pair or not patch_info_pair.manifest_info:
            return

        manifest_url = patch_info_pair.manifest_info.manifest_file_url
        async with http_client.get(manifest_url) as response:
            response.raise_for_status()
            data = await response.read()

        if patch_info_pair.manifest_info.is_use_compression:
            import zstandard
            dctx = zstandard.ZstdDecompressor()
            data = dctx.decompress(data)

        from .proto.SophonPatchProto_pb2 import SophonPatchProto
        patch_proto = SophonPatchProto()
        patch_proto.ParseFromString(data)

        for patch_prop in patch_proto.PatchAssets:
            target_chunk = None
            for info in patch_prop.AssetInfos:
                if info.VersionTag == version_tag_update_from:
                    target_chunk = info.Chunk
                    break

            if not target_chunk:
                continue

            yield SophonPatchAsset(
                patch_name_source=target_chunk.PatchName,
                patch_hash=target_chunk.PatchMd5,
                patch_offset=target_chunk.PatchOffset,
                patch_size=target_chunk.PatchSize,
                patch_chunk_length=target_chunk.PatchLength,
                original_file_path=target_chunk.OriginalFileName,
                original_file_hash=target_chunk.OriginalFileMd5,
                original_file_size=target_chunk.OriginalFileLength,
                target_file_path=patch_prop.AssetName,
                target_file_hash=patch_prop.AssetHashMd5,
                target_file_size=patch_prop.AssetSize,
                patch_method=SophonPatchMethod.PATCH
            )

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
        try:
            async with client.get(url) as response:
                response.raise_for_status()
                json_data = await response.json()
        except Exception as e:
            return SophonChunkManifestInfoPair(is_found=False, return_message=str(e))

        if not isinstance(json_data, dict):
            return SophonChunkManifestInfoPair(is_found=False, return_message="Invalid API response")

        if "retcode" not in json_data:
            return SophonChunkManifestInfoPair(is_found=False, return_message="Missing retcode")

        if json_data["retcode"] != 0:
            error_msg = json_data.get("message", "Unknown API error")
            return SophonChunkManifestInfoPair(is_found=False, return_message=f"API error: {error_msg}")

        if "data" not in json_data or not isinstance(json_data["data"], dict):
            return SophonChunkManifestInfoPair(is_found=False, return_message="Missing data field")

        data = json_data["data"]
        if "manifests" not in data or not isinstance(data["manifests"], list):
            return SophonChunkManifestInfoPair(is_found=False, return_message="Missing manifests field")

        manifests = data["manifests"]

        target_manifest = None
        for m in manifests:
            if matching_field and m.get("matching_field") != matching_field:
                continue
            patches = m.get("patches", [])
            for p in patches:
                if p.get("version_tag") == version_tag_update_from:
                    target_manifest = p
                    break
            if target_manifest:
                break

        if not target_manifest:
            return SophonChunkManifestInfoPair(is_found=False, return_message="Patch not found")

        patch_manifest = target_manifest.get("patch", {})
        md = target_manifest.get("patch_download", {})
        cd = target_manifest.get("chunk_download", {})
        stats = target_manifest.get("stats", {})

        from .manifest import SophonManifest
        manifest_info = SophonManifest.create_manifest_info(
            manifest_base_url=md.get("url_prefix", ""),
            manifest_checksum_md5=patch_manifest.get("checksum", ""),
            manifest_id=patch_manifest.get("id", ""),
            is_use_compression=md.get("compression", 0) == 1,
            manifest_size=int(patch_manifest.get("uncompressed_size", 0) or 0),
            manifest_compressed_size=int(patch_manifest.get("compressed_size", 0) or 0),
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
