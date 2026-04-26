"""SophonAsset for downloading files using Sophon protocol."""

import asyncio
import hashlib
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import BinaryIO, Callable, Optional, Union

import aiohttp
import zstandard

from .chunk import ParallelOptions, SophonChunk
from .exceptions import DownloadError
from .speed_limiter import SophonDownloadSpeedLimiter
from .types import IdentifiableProperty
from .types.chunks_info import SophonChunksInfo

logger = logging.getLogger(__name__)

# Default retry attempts and timeout
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT_SECONDS = 30


class ZstdDecompressionStream:
    """Async wrapper to decompress zstd streams from aiohttp."""

    def __init__(self, reader: aiohttp.StreamReader):
        self.reader = reader
        self.decompressor = zstandard.ZstdDecompressor()
        self.decompressobj = self.decompressor.decompressobj()
        self.buffer = bytearray()

    async def read(self, n: int = -1) -> bytes:
        if n == -1:
            n = float('inf')

        while len(self.buffer) < n:
            chunk = await self.reader.read(8192)
            if not chunk:
                break
            try:
                decompressed = self.decompressobj.decompress(chunk)
                if decompressed:
                    self.buffer.extend(decompressed)
            except zstandard.ZstdError as e:
                raise DownloadError(f"Decompression error: {e}") from e

        if n == float('inf'):
            res = bytes(self.buffer)
            self.buffer.clear()
            return res

        res = bytes(self.buffer[:n])
        self.buffer = self.buffer[n:]
        return res


class SourceStreamType(Enum):
    """Type of source stream for downloading."""

    INTERNET = "internet"
    CACHED_LOCAL = "cached_local"
    OLD_REFERENCE = "old_reference"


@dataclass
class SophonAsset(IdentifiableProperty):
    """Represents a single asset (file) to be downloaded."""

    asset_name: str = ""
    asset_size: int = 0
    asset_hash: Optional[str] = None
    is_directory: bool = False
    is_has_patch: bool = False
    chunks: list[SophonChunk] = field(default_factory=list)
    download_speed_limiter: Optional[SophonDownloadSpeedLimiter] = None
    sophon_chunks_info: Optional[SophonChunksInfo] = None
    sophon_chunks_info_alt: Optional[SophonChunksInfo] = None

    BUFFER_SIZE = 4 * 1024  # 4 KB buffer

    def _validate_chunks_state(self) -> None:
        """Validate that chunks are properly initialized."""
        if not self.chunks:
            raise ValueError(f"Asset {self.asset_name} has no chunks initialized")

    def _validate_stream_state(self, stream: aiohttp.StreamReader) -> None:
        """Validate that stream is properly initialized."""
        if stream is None:
            raise ValueError("Stream cannot be None")

    async def write_to_stream_async(
        self,
        client: aiohttp.ClientSession,
        output_path: str,
        parallel_options: Optional[ParallelOptions] = None,
        write_info_delegate: Optional[Callable[[int], None]] = None,
        download_info_delegate: Optional[Callable[[int, int], None]] = None,
        download_complete_delegate: Optional[Callable[["SophonAsset"], None]] = None,
        token: Optional[asyncio.CancelledError] = None,
    ) -> None:
        """
        Download asset file by writing chunks to output path.

        Args:
            client: aiohttp ClientSession for downloads.
            output_path: Path where file will be written.
            parallel_options: Parallel execution options.
            write_info_delegate: Callback for write info updates (bytes written).
            download_info_delegate: Callback for download progress (total, network).
            download_complete_delegate: Callback when download completes.
            token: Cancellation token.

        Raises:
            ValueError: If chunks are not properly initialized.
            IOError: If file operations fail.
            DownloadError: If download fails.
        """
        self._validate_chunks_state()

        if token is None:
            token = asyncio.CancelledError()

        # Create or truncate the output file
        try:
            with open(output_path, "wb") as f:
                if self.asset_size > 0:
                    f.truncate(self.asset_size)
        except OSError as e:
            raise OSError(f"Failed to create output file at {output_path}: {e}")

        # Download chunks
        try:
            if parallel_options and parallel_options.max_degree_of_parallelism > 1:
                semaphore = asyncio.Semaphore(parallel_options.max_degree_of_parallelism)

                async def _download_chunk(chunk):
                    async with semaphore:
                        with open(output_path, "r+b") as stream:
                            await self._perform_write_stream_thread_async(
                                client,
                                None,
                                SourceStreamType.INTERNET,
                                stream,
                                chunk,
                                write_info_delegate,
                                download_info_delegate,
                                token,
                            )

                tasks = [_download_chunk(chunk) for chunk in self.chunks]
                await asyncio.gather(*tasks)
            else:
                with open(output_path, "r+b") as stream:
                    for chunk in self.chunks:
                        await self._perform_write_stream_thread_async(
                            client,
                            None,
                            SourceStreamType.INTERNET,
                            stream,
                            chunk,
                            write_info_delegate,
                            download_info_delegate,
                            token,
                        )

            logger.info(
                f"Asset: {self.asset_name} ({self.asset_size} bytes) "
                f"has been completely downloaded!"
            )
            if download_complete_delegate:
                download_complete_delegate(self)

        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to download asset {self.asset_name} to {output_path}: {e}"
            )
            raise DownloadError(
                f"Failed to download asset {self.asset_name}: {e}"
            ) from e

    async def download_diff_chunks_async(
        self,
        client: aiohttp.ClientSession,
        chunk_dir_output: str,
        parallel_options: Optional[ParallelOptions] = None,
        write_info_delegate: Optional[Callable[[int], None]] = None,
        download_info_delegate: Optional[Callable[[int, int], None]] = None,
        download_complete_delegate: Optional[Callable[[str], None]] = None,
        force_verification: bool = False,
    ) -> None:
        """
        Download and stage diff chunks for update/preload operations.

        Args:
            client: aiohttp ClientSession for downloads.
            chunk_dir_output: Directory to store staged chunks.
            parallel_options: Parallel execution options.
            write_info_delegate: Callback for write info updates.
            download_info_delegate: Callback for download progress.
            download_complete_delegate: Callback when download completes.
            force_verification: Force verification of chunks.

        Raises:
            ValueError: If chunks are not properly initialized.
            IOError: If directory operations fail.
        """
        import os
        self._validate_chunks_state()
        if token := getattr(parallel_options, "cancellation_token", None):
            # TODO: handle custom cancellation tokens properly if passed in parallel_options
            pass
        else:
            token = asyncio.CancelledError()

        os.makedirs(chunk_dir_output, exist_ok=True)

        async def _download_diff_chunk(chunk: SophonChunk):
            if chunk.chunk_old_offset != -1:
                return  # It's an old chunk, no need to download

            chunk_path = os.path.join(chunk_dir_output, chunk.chunk_name)

            # Check if chunk exists and is valid
            is_valid = False
            if os.path.exists(chunk_path):
                with open(chunk_path, "rb") as f:
                    is_valid = await chunk.check_chunk_hash_async(f, False)

            if is_valid and not force_verification:
                logger.debug(f"Chunk {chunk.chunk_name} already downloaded and valid")
                if write_info_delegate:
                    write_info_delegate(chunk.chunk_size_decompressed)
                if download_info_delegate:
                    download_info_delegate(chunk.chunk_size_decompressed, 0)
                return

            with open(chunk_path, "wb") as f:
                pass  # Create empty file

            with open(chunk_path, "r+b") as stream:
                await self._perform_write_stream_thread_async(
                    client,
                    None,
                    SourceStreamType.INTERNET,
                    stream,
                    chunk,
                    write_info_delegate,
                    download_info_delegate,
                    token,
                )

        try:
            if parallel_options and parallel_options.max_degree_of_parallelism > 1:
                semaphore = asyncio.Semaphore(parallel_options.max_degree_of_parallelism)

                async def _bounded_download(chunk):
                    async with semaphore:
                        await _download_diff_chunk(chunk)

                tasks = [_bounded_download(chunk) for chunk in self.chunks]
                await asyncio.gather(*tasks)
            else:
                for chunk in self.chunks:
                    await _download_diff_chunk(chunk)

            if download_complete_delegate:
                download_complete_delegate(self.asset_name)

        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Failed to download diff chunks for {self.asset_name}: {e}")
            raise DownloadError(f"Failed to download diff chunks: {e}") from e

    async def write_update_async(
        self,
        client: aiohttp.ClientSession,
        old_input_dir: str,
        new_output_dir: str,
        chunk_dir: str,
        remove_chunk_after_apply: bool = False,
        write_info_delegate: Optional[Callable[[int], None]] = None,
        download_info_delegate: Optional[Callable[[int, int], None]] = None,
        download_complete_delegate: Optional[Callable[[str], None]] = None,
        token: Optional[asyncio.CancelledError] = None,
    ) -> None:
        """
        Apply update to existing or new file.

        Args:
            client: aiohttp ClientSession for downloads.
            old_input_dir: Directory containing old version.
            new_output_dir: Directory for new version.
            chunk_dir: Directory with staged chunks.
            remove_chunk_after_apply: Remove chunks after applying update.
            write_info_delegate: Callback for write info updates.
            download_info_delegate: Callback for download progress.
            download_complete_delegate: Callback when update completes.
            token: Cancellation token.

        Raises:
            ValueError: If input directories don't exist.
            IOError: If file operations fail.
        """
        import os
        self._validate_chunks_state()
        if token is None:
            token = asyncio.CancelledError()

        old_path = os.path.join(old_input_dir, self.asset_name)
        new_path = os.path.join(new_output_dir, self.asset_name)

        if not os.path.exists(old_path) and any(c.chunk_old_offset != -1 for c in self.chunks):
            raise ValueError(f"Old file not found: {old_path}")

        os.makedirs(os.path.dirname(new_path) or ".", exist_ok=True)
        try:
            with open(new_path, "wb") as f:
                if self.asset_size > 0:
                    f.truncate(self.asset_size)
        except OSError as e:
            raise OSError(f"Failed to create new file at {new_path}: {e}")

        old_stream = None
        try:
            old_stream = open(old_path, "rb") if os.path.exists(old_path) else None
            with open(new_path, "r+b") as new_stream:
                for chunk in self.chunks:
                    if chunk.chunk_old_offset != -1:
                        await self._perform_write_stream_thread_async(
                            client,
                            old_stream,
                            SourceStreamType.OLD_REFERENCE,
                            new_stream,
                            chunk,
                            write_info_delegate,
                            download_info_delegate,
                            token,
                        )
                    else:
                        chunk_path = os.path.join(chunk_dir, chunk.chunk_name)
                        if not os.path.exists(chunk_path):
                            # Try to download it from internet directly if not staged
                            await self._perform_write_stream_thread_async(
                                client,
                                None,
                                SourceStreamType.INTERNET,
                                new_stream,
                                chunk,
                                write_info_delegate,
                                download_info_delegate,
                                token,
                            )
                        else:
                            with open(chunk_path, "rb") as cached_stream:
                                await self._perform_write_stream_thread_async(
                                    client,
                                    cached_stream,
                                    SourceStreamType.CACHED_LOCAL,
                                    new_stream,
                                    chunk,
                                    write_info_delegate,
                                    download_info_delegate,
                                    token,
                                    write_offset=-1,
                                )
                            if remove_chunk_after_apply:
                                try:
                                    os.remove(chunk_path)
                                except OSError:
                                    pass

            if download_complete_delegate:
                download_complete_delegate(self.asset_name)

        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Failed to apply update for {self.asset_name}: {e}")
            raise DownloadError(f"Failed to apply update: {e}") from e
        finally:
            if old_stream:
                old_stream.close()

    async def _perform_write_stream_thread_async(
        self,
        client: aiohttp.ClientSession,
        source_stream: Optional[BinaryIO],
        source_stream_type: SourceStreamType,
        out_stream: BinaryIO,
        chunk: SophonChunk,
        write_info_delegate: Optional[Callable[[int], None]],
        download_info_delegate: Optional[Callable[[int, int], None]],
        token: asyncio.CancelledError,
        write_offset: int = -1,
    ) -> None:
        """
        Perform a single chunk download/write operation.

        Args:
            client: HTTP client for downloads.
            source_stream: Source stream for non-internet sources.
            source_stream_type: Type of source stream.
            out_stream: Output file stream.
            chunk: Chunk to download.
            write_info_delegate: Write progress callback.
            download_info_delegate: Download progress callback.
            token: Cancellation token.
        """
        actual_offset = write_offset if write_offset != -1 else chunk.chunk_offset
        total_size_from_offset = actual_offset + chunk.chunk_size_decompressed
        is_skip_chunk = False

        # Check if chunk already exists and is valid
        if out_stream.seek(0, 2) >= total_size_from_offset:
            out_stream.seek(actual_offset)
            is_skip_chunk = await chunk.check_chunk_hash_async(out_stream, False)

        if is_skip_chunk:
            logger.debug(
                f"Skipping chunk 0x{chunk.chunk_offset:08x} "
                f"-> L: 0x{chunk.chunk_size_decompressed:08x} for: {self.asset_name}"
            )
            if write_info_delegate:
                write_info_delegate(chunk.chunk_size_decompressed)

            download_bytes = 0 if chunk.chunk_old_offset != -1 else chunk.chunk_size_decompressed
            if download_info_delegate:
                download_info_delegate(download_bytes, 0)
            return

        # Perform the actual download
        await self._inner_write_stream_to_async(
            client,
            source_stream,
            source_stream_type,
            out_stream,
            chunk,
            write_info_delegate,
            download_info_delegate,
            token,
        )

    async def _inner_write_stream_to_async(
        self,
        client: aiohttp.ClientSession,
        source_stream: Optional[BinaryIO],
        source_stream_type: SourceStreamType,
        out_stream: BinaryIO,
        chunk: SophonChunk,
        write_info_delegate: Optional[Callable[[int], None]],
        download_info_delegate: Optional[Callable[[int, int], None]],
        token: asyncio.CancelledError,
        write_offset: int = -1,
    ) -> None:
        """
        Core download logic with retries and error handling.

        Args:
            client: HTTP client for downloads.
            source_stream: Source stream for non-internet sources.
            source_stream_type: Type of source stream.
            out_stream: Output file stream.
            chunk: Chunk to download.
            write_info_delegate: Write progress callback.
            download_info_delegate: Download progress callback.
            token: Cancellation token.
        """
        if (
            source_stream_type != SourceStreamType.INTERNET
            and source_stream is None
        ):
            raise ValueError(
                "Source stream cannot be None for CachedLocal or OldReference mode"
            )

        if (
            source_stream_type == SourceStreamType.OLD_REFERENCE
            and chunk.chunk_old_offset < 0
        ):
            raise ValueError(
                "OldReference mode requires chunk to have chunk_old_offset set"
            )

        current_retry = 0
        current_write_offset = 0
        current_source_stream_type = source_stream_type
        http_response: Optional[aiohttp.ClientResponse] = None

        while True:
            allow_dispose = False

            try:
                # Create timeout
                timeout = aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT_SECONDS)

                logger.debug(
                    f"Init. by offset: 0x{chunk.chunk_offset:08x} "
                    f"-> L: 0x{chunk.chunk_size_decompressed:08x} "
                    f"for chunk: {chunk.chunk_name}"
                )

                out_stream.seek(chunk.chunk_offset)

                md5_hash = hashlib.md5()
                buffer = bytearray(self.BUFFER_SIZE)
                current_source_stream: Optional[Union[aiohttp.StreamReader, BinaryIO]] = None

                # Setup source stream based on type
                if current_source_stream_type == SourceStreamType.INTERNET:
                    try:
                        # Download from internet
                        if self.sophon_chunks_info is None:
                            raise ValueError("sophon_chunks_info is not set")

                        http_response = await client.get(
                            f"{self.sophon_chunks_info.chunks_base_url}/{chunk.chunk_name}",
                            timeout=timeout,
                            raise_for_status=True,
                        )
                        current_source_stream = http_response.content

                        if self.sophon_chunks_info.is_use_compression:
                            current_source_stream = ZstdDecompressionStream(http_response.content)

                    except aiohttp.ClientError as e:
                        if current_retry < DEFAULT_RETRY_ATTEMPTS:
                            current_retry += 1
                            logger.warning(
                                f"Network error downloading chunk {chunk.chunk_name}: {e}. "
                                f"Retry {current_retry}/{DEFAULT_RETRY_ATTEMPTS}"
                            )
                            await asyncio.sleep(1)
                            if http_response:
                                http_response.close()
                            continue
                        raise DownloadError(f"Failed to download chunk {chunk.chunk_name}: {e}")

                elif current_source_stream_type == SourceStreamType.CACHED_LOCAL:
                    # Use cached local source
                    current_source_stream = source_stream
                    # TODO: Handle decompression if needed

                elif current_source_stream_type == SourceStreamType.OLD_REFERENCE:
                    # Reference old file
                    current_source_stream = source_stream
                    if current_source_stream:
                        current_source_stream.seek(chunk.chunk_old_offset)

                logger.debug(
                    f"[Complete init.] by offset: 0x{chunk.chunk_offset:08x} "
                    f"-> L: 0x{chunk.chunk_size_decompressed:08x} "
                    f"for chunk: {chunk.chunk_name}"
                )

                # Read and write data
                remain = chunk.chunk_size_decompressed
                while remain > 0:
                    to_read = min(len(buffer), remain)

                    # Read data based on stream type
                    if isinstance(current_source_stream, (aiohttp.StreamReader, ZstdDecompressionStream)):
                        data = await current_source_stream.read(to_read)
                    elif current_source_stream is not None:
                        # File stream or other stream type
                        data = current_source_stream.read(to_read)
                    else:
                        raise ValueError("Source stream is None")

                    if not data and remain > 0:
                        if current_retry < DEFAULT_RETRY_ATTEMPTS:
                            current_retry += 1
                            if write_info_delegate:
                                write_info_delegate(-current_write_offset)
                            if source_stream_type != SourceStreamType.OLD_REFERENCE and download_info_delegate:
                                download_info_delegate(-current_write_offset, 0)
                            current_write_offset = 0
                            logger.warning(
                                f"Incomplete read for chunk {chunk.chunk_name}. "
                                f"Retry {current_retry}/{DEFAULT_RETRY_ATTEMPTS}"
                            )
                            await asyncio.sleep(1)
                            break
                        raise DownloadError(
                            f"Incomplete chunk download: {remain} bytes remaining"
                        )

                    if current_source_stream_type == SourceStreamType.INTERNET:
                        if self.download_speed_limiter:
                            await self.download_speed_limiter.add_bytes_or_wait_async(len(data), token)

                    out_stream.write(data)
                    current_write_offset += len(data)
                    remain -= len(data)
                    md5_hash.update(data)
                    if write_info_delegate:
                        write_info_delegate(len(data))

                    if source_stream_type != SourceStreamType.OLD_REFERENCE and download_info_delegate:
                        net_bytes = len(data) if current_source_stream_type == SourceStreamType.INTERNET else 0
                        download_info_delegate(len(data), net_bytes)

                    current_retry = 0
                    await asyncio.sleep(0)

                # Verify hash
                calculated_hash = md5_hash.digest()
                if calculated_hash != chunk.chunk_hash_decompressed:
                    if write_info_delegate:
                        write_info_delegate(-current_write_offset)
                    if source_stream_type != SourceStreamType.OLD_REFERENCE and download_info_delegate:
                        download_info_delegate(-current_write_offset, 0)

                    allow_dispose = True
                    logger.warning(
                        f"Hash verification failed for chunk {chunk.chunk_name}. "
                        f"Retrying download."
                    )
                    current_source_stream_type = SourceStreamType.INTERNET
                    current_write_offset = 0
                    continue

                logger.debug(
                    f"Download completed! Chunk: {chunk.chunk_name} "
                    f"| 0x{chunk.chunk_offset:08x} -> "
                    f"L: 0x{chunk.chunk_size_decompressed:08x} for: {self.asset_name}"
                )
                allow_dispose = True
                return

            except asyncio.CancelledError:
                allow_dispose = True
                raise

            except Exception as ex:
                if http_response:
                    http_response.close()

                last_source_stream_type = current_source_stream_type
                current_source_stream_type = SourceStreamType.INTERNET

                if current_retry < DEFAULT_RETRY_ATTEMPTS:
                    if write_info_delegate:
                        write_info_delegate(-current_write_offset)
                    if last_source_stream_type != SourceStreamType.OLD_REFERENCE and download_info_delegate:
                        download_info_delegate(-current_write_offset, 0)

                    current_write_offset = 0
                    current_retry += 1

                    logger.warning(
                        f"Error downloading chunk {chunk.chunk_name}: {ex}. "
                        f"Retry {current_retry}/{DEFAULT_RETRY_ATTEMPTS}"
                    )
                    await asyncio.sleep(1)
                    continue

                allow_dispose = True
                logger.error(
                    f"Failed to download chunk {chunk.chunk_name} "
                    f"after {DEFAULT_RETRY_ATTEMPTS} retries: {ex}"
                )
                raise DownloadError(f"Failed to download chunk {chunk.chunk_name}: {ex}") from ex

            finally:
                if allow_dispose:
                    if http_response:
                        http_response.close()

    def __str__(self) -> str:
        """Return asset name as string representation."""
        return self.asset_name

    def __hash__(self) -> int:
        """Return hash based on asset properties."""
        return hash((self.is_has_patch, self.asset_name, self.asset_hash))
