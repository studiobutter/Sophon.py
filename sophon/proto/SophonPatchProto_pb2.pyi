from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SophonPatchProto(_message.Message):
    __slots__ = ("PatchAssets", "UnusedAssets")
    PATCHASSETS_FIELD_NUMBER: _ClassVar[int]
    UNUSEDASSETS_FIELD_NUMBER: _ClassVar[int]
    PatchAssets: _containers.RepeatedCompositeFieldContainer[SophonPatchAssetProperty]
    UnusedAssets: _containers.RepeatedCompositeFieldContainer[SophonUnusedAssetProperty]
    def __init__(self, PatchAssets: _Optional[_Iterable[_Union[SophonPatchAssetProperty, _Mapping]]] = ..., UnusedAssets: _Optional[_Iterable[_Union[SophonUnusedAssetProperty, _Mapping]]] = ...) -> None: ...

class SophonPatchAssetProperty(_message.Message):
    __slots__ = ("AssetName", "AssetSize", "AssetHashMd5", "AssetInfos")
    ASSETNAME_FIELD_NUMBER: _ClassVar[int]
    ASSETSIZE_FIELD_NUMBER: _ClassVar[int]
    ASSETHASHMD5_FIELD_NUMBER: _ClassVar[int]
    ASSETINFOS_FIELD_NUMBER: _ClassVar[int]
    AssetName: str
    AssetSize: int
    AssetHashMd5: str
    AssetInfos: _containers.RepeatedCompositeFieldContainer[SophonPatchAssetInfo]
    def __init__(self, AssetName: _Optional[str] = ..., AssetSize: _Optional[int] = ..., AssetHashMd5: _Optional[str] = ..., AssetInfos: _Optional[_Iterable[_Union[SophonPatchAssetInfo, _Mapping]]] = ...) -> None: ...

class SophonPatchAssetInfo(_message.Message):
    __slots__ = ("VersionTag", "Chunk")
    VERSIONTAG_FIELD_NUMBER: _ClassVar[int]
    CHUNK_FIELD_NUMBER: _ClassVar[int]
    VersionTag: str
    Chunk: SophonPatchAssetChunk
    def __init__(self, VersionTag: _Optional[str] = ..., Chunk: _Optional[_Union[SophonPatchAssetChunk, _Mapping]] = ...) -> None: ...

class SophonPatchAssetChunk(_message.Message):
    __slots__ = ("PatchName", "VersionTag", "BuildId", "PatchSize", "PatchMd5", "PatchOffset", "PatchLength", "OriginalFileName", "OriginalFileLength", "OriginalFileMd5")
    PATCHNAME_FIELD_NUMBER: _ClassVar[int]
    VERSIONTAG_FIELD_NUMBER: _ClassVar[int]
    BUILDID_FIELD_NUMBER: _ClassVar[int]
    PATCHSIZE_FIELD_NUMBER: _ClassVar[int]
    PATCHMD5_FIELD_NUMBER: _ClassVar[int]
    PATCHOFFSET_FIELD_NUMBER: _ClassVar[int]
    PATCHLENGTH_FIELD_NUMBER: _ClassVar[int]
    ORIGINALFILENAME_FIELD_NUMBER: _ClassVar[int]
    ORIGINALFILELENGTH_FIELD_NUMBER: _ClassVar[int]
    ORIGINALFILEMD5_FIELD_NUMBER: _ClassVar[int]
    PatchName: str
    VersionTag: str
    BuildId: str
    PatchSize: int
    PatchMd5: str
    PatchOffset: int
    PatchLength: int
    OriginalFileName: str
    OriginalFileLength: int
    OriginalFileMd5: str
    def __init__(self, PatchName: _Optional[str] = ..., VersionTag: _Optional[str] = ..., BuildId: _Optional[str] = ..., PatchSize: _Optional[int] = ..., PatchMd5: _Optional[str] = ..., PatchOffset: _Optional[int] = ..., PatchLength: _Optional[int] = ..., OriginalFileName: _Optional[str] = ..., OriginalFileLength: _Optional[int] = ..., OriginalFileMd5: _Optional[str] = ...) -> None: ...

class SophonUnusedAssetProperty(_message.Message):
    __slots__ = ("VersionTag", "AssetInfos")
    VERSIONTAG_FIELD_NUMBER: _ClassVar[int]
    ASSETINFOS_FIELD_NUMBER: _ClassVar[int]
    VersionTag: str
    AssetInfos: _containers.RepeatedCompositeFieldContainer[SophonUnusedAssetInfo]
    def __init__(self, VersionTag: _Optional[str] = ..., AssetInfos: _Optional[_Iterable[_Union[SophonUnusedAssetInfo, _Mapping]]] = ...) -> None: ...

class SophonUnusedAssetInfo(_message.Message):
    __slots__ = ("Assets",)
    ASSETS_FIELD_NUMBER: _ClassVar[int]
    Assets: _containers.RepeatedCompositeFieldContainer[SophonUnusedAssetFile]
    def __init__(self, Assets: _Optional[_Iterable[_Union[SophonUnusedAssetFile, _Mapping]]] = ...) -> None: ...

class SophonUnusedAssetFile(_message.Message):
    __slots__ = ("FileName", "FileSize", "FileMd5")
    FILENAME_FIELD_NUMBER: _ClassVar[int]
    FILESIZE_FIELD_NUMBER: _ClassVar[int]
    FILEMD5_FIELD_NUMBER: _ClassVar[int]
    FileName: str
    FileSize: int
    FileMd5: str
    def __init__(self, FileName: _Optional[str] = ..., FileSize: _Optional[int] = ..., FileMd5: _Optional[str] = ...) -> None: ...
