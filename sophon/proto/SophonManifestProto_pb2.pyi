from collections.abc import Iterable as _Iterable
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf.internal import containers as _containers

DESCRIPTOR: _descriptor.FileDescriptor

class SophonManifestProto(_message.Message):
    __slots__ = ("Assets",)
    ASSETS_FIELD_NUMBER: _ClassVar[int]
    Assets: _containers.RepeatedCompositeFieldContainer[SophonManifestAssetProperty]
    def __init__(self, Assets: _Iterable[SophonManifestAssetProperty | _Mapping] | None = ...) -> None: ...

class SophonManifestAssetProperty(_message.Message):
    __slots__ = ("AssetName", "AssetChunks", "AssetType", "AssetSize", "AssetHashMd5")
    ASSETNAME_FIELD_NUMBER: _ClassVar[int]
    ASSETCHUNKS_FIELD_NUMBER: _ClassVar[int]
    ASSETTYPE_FIELD_NUMBER: _ClassVar[int]
    ASSETSIZE_FIELD_NUMBER: _ClassVar[int]
    ASSETHASHMD5_FIELD_NUMBER: _ClassVar[int]
    AssetName: str
    AssetChunks: _containers.RepeatedCompositeFieldContainer[SophonManifestAssetChunk]
    AssetType: int
    AssetSize: int
    AssetHashMd5: str
    def __init__(self, AssetName: str | None = ..., AssetChunks: _Iterable[SophonManifestAssetChunk | _Mapping] | None = ..., AssetType: int | None = ..., AssetSize: int | None = ..., AssetHashMd5: str | None = ...) -> None: ...

class SophonManifestAssetChunk(_message.Message):
    __slots__ = ("ChunkName", "ChunkDecompressedHashMd5", "ChunkOnFileOffset", "ChunkSize", "ChunkSizeDecompressed")
    CHUNKNAME_FIELD_NUMBER: _ClassVar[int]
    CHUNKDECOMPRESSEDHASHMD5_FIELD_NUMBER: _ClassVar[int]
    CHUNKONFILEOFFSET_FIELD_NUMBER: _ClassVar[int]
    CHUNKSIZE_FIELD_NUMBER: _ClassVar[int]
    CHUNKSIZEDECOMPRESSED_FIELD_NUMBER: _ClassVar[int]
    ChunkName: str
    ChunkDecompressedHashMd5: str
    ChunkOnFileOffset: int
    ChunkSize: int
    ChunkSizeDecompressed: int
    def __init__(self, ChunkName: str | None = ..., ChunkDecompressedHashMd5: str | None = ..., ChunkOnFileOffset: int | None = ..., ChunkSize: int | None = ..., ChunkSizeDecompressed: int | None = ...) -> None: ...
