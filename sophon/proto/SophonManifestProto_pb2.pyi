from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SophonManifestProto(_message.Message):
    __slots__ = ("Assets",)
    ASSETS_FIELD_NUMBER: _ClassVar[int]
    Assets: _containers.RepeatedCompositeFieldContainer[SophonManifestAssetProperty]
    def __init__(self, Assets: _Optional[_Iterable[_Union[SophonManifestAssetProperty, _Mapping]]] = ...) -> None: ...

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
    def __init__(self, AssetName: _Optional[str] = ..., AssetChunks: _Optional[_Iterable[_Union[SophonManifestAssetChunk, _Mapping]]] = ..., AssetType: _Optional[int] = ..., AssetSize: _Optional[int] = ..., AssetHashMd5: _Optional[str] = ...) -> None: ...

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
    def __init__(self, ChunkName: _Optional[str] = ..., ChunkDecompressedHashMd5: _Optional[str] = ..., ChunkOnFileOffset: _Optional[int] = ..., ChunkSize: _Optional[int] = ..., ChunkSizeDecompressed: _Optional[int] = ...) -> None: ...
