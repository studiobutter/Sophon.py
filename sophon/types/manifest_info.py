"""Manifest information structures."""

from dataclasses import dataclass

from . import IdentifiableProperty


@dataclass
class SophonManifestInfo(IdentifiableProperty):
    """Information about a Sophon manifest file."""

    manifest_base_url: str = ""
    manifest_id: str = ""
    manifest_checksum_md5: str = ""
    is_use_compression: bool = False
    manifest_size: int = 0
    manifest_compressed_size: int = 0

    @property
    def manifest_file_url(self) -> str:
        """Get the full manifest file URL."""
        base = self.manifest_base_url.rstrip("/")
        return f"{base}/{self.manifest_id}"
