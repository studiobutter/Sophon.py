"""Chunks information structures."""

from dataclasses import dataclass
from typing import Optional

from . import IdentifiableProperty


@dataclass
class SophonChunksInfo(IdentifiableProperty):
    """Information about Sophon chunks for downloading."""

    chunks_base_url: Optional[str] = None
    chunks_count: int = 0
    files_count: int = 0
    total_size: int = 0
    total_compressed_size: int = 0
    is_use_compression: bool = False

    def __eq__(self, other: object) -> bool:
        """Check equality of chunks info."""
        if not isinstance(other, SophonChunksInfo):
            return NotImplemented
        return (
            self.chunks_base_url == other.chunks_base_url
            and self.chunks_count == other.chunks_count
            and self.files_count == other.files_count
            and self.total_size == other.total_size
            and self.total_compressed_size == other.total_compressed_size
            and self.is_use_compression == other.is_use_compression
        )

    def __hash__(self) -> int:
        """Make the object hashable."""
        return hash(
            (
                self.chunks_base_url,
                self.chunks_count,
                self.files_count,
                self.total_size,
                self.total_compressed_size,
                self.is_use_compression,
            )
        )
