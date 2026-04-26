"""Chunk structure and utilities."""

import asyncio
import hashlib
from dataclasses import dataclass
from typing import BinaryIO, Optional


@dataclass
class SophonChunk:
    """Represents a single chunk of a file for download."""

    chunk_name: str
    chunk_hash_decompressed: bytes
    chunk_offset: int
    chunk_size: int
    chunk_size_decompressed: int
    chunk_old_offset: int = -1  # -1 means no reference to old file
    is_skip_hash_check_on_write: bool = False

    BUFFER_SIZE = 4 * 1024  # 4 KB buffer

    def __post_init__(self) -> None:
        """Validate chunk after initialization."""
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if self.chunk_size_decompressed <= 0:
            raise ValueError("chunk_size_decompressed must be greater than 0")

    async def check_chunk_hash_async(
        self,
        stream: BinaryIO,
        verify_from_offset: bool = False,
    ) -> bool:
        """
        Verify chunk hash asynchronously.

        Args:
            stream: Stream to verify from.
            verify_from_offset: If True, verify from chunk offset; otherwise from current position.

        Returns:
            True if hash matches, False otherwise.
        """
        md5_hash = hashlib.md5()

        if verify_from_offset:
            stream.seek(self.chunk_offset)

        bytes_read = 0
        while bytes_read < self.chunk_size_decompressed:
            to_read = min(self.BUFFER_SIZE, self.chunk_size_decompressed - bytes_read)
            data = stream.read(to_read)

            if not data:
                return False

            md5_hash.update(data)
            bytes_read += len(data)

            # Allow other tasks to run
            await asyncio.sleep(0)

        return md5_hash.digest() == self.chunk_hash_decompressed


@dataclass
class ParallelOptions:
    """Options for parallel operations."""

    max_degree_of_parallelism: int = 4
    cancellation_token: Optional[object] = None

    def __post_init__(self) -> None:
        """Validate options after initialization."""
        if self.max_degree_of_parallelism < 1:
            raise ValueError("max_degree_of_parallelism must be at least 1")
