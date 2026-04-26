"""Manifest and chunks info pair structure."""

from dataclasses import dataclass, field
from typing import Optional

from . import IdentifiableProperty
from .chunks_info import SophonChunksInfo
from .manifest_info import SophonManifestInfo


@dataclass
class SophonManifestBuildData(IdentifiableProperty):
    """Data about a Sophon manifest build."""

    build_id: Optional[str] = None
    tag_name: Optional[str] = None
    manifest_identity_list: list = field(default_factory=list)


@dataclass
class SophonManifestPatchData(IdentifiableProperty):
    """Data about a Sophon manifest patch."""

    build_id: Optional[str] = None
    tag_name: Optional[str] = None
    patch_id: Optional[str] = None
    manifest_identity_list: list = field(default_factory=list)


@dataclass
class SophonChunkManifestInfoPair(IdentifiableProperty):
    """Pair of manifest and chunks information."""

    chunks_info: Optional[SophonChunksInfo] = None
    manifest_info: Optional[SophonManifestInfo] = None
    other_sophon_build_data: Optional[SophonManifestBuildData] = None
    other_sophon_patch_data: Optional[SophonManifestPatchData] = None
    is_found: bool = True
    return_code: int = 0
    return_message: Optional[str] = None

    def __str__(self) -> str:
        """String representation of the pair."""
        return f"{self.category_id} - {self.matching_field} ({self.category_name})"
