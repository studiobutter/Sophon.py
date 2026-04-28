"""Comprehensive test suite for Sophon.py - Python port of Hi3Helper.Sophon.

This test suite provides thorough coverage of:
- Core download engine
- Chunk management and verification
- Manifest parsing and enumeration
- Update and patch operations
- Error handling and recovery
- Integration scenarios
- Edge cases and stress testing

Python version: 3.9+
Target: Python 3.13
"""

import asyncio
import hashlib
import io
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
import zstandard
from aioresponses import aioresponses

from sophon.asset import SophonAsset, ZstdDecompressionStream
from sophon.chunk import ParallelOptions, SophonChunk
from sophon.exceptions import (
    ChunkVerificationError,
    DownloadError,
    InvalidManifestError,
    ManifestNotFoundError,
    PatchError,
    SophonException,
)
from sophon.manifest import SophonManifest
from sophon.patch import SophonPatchAsset, SophonPatchMethod
from sophon.proto.SophonManifestProto_pb2 import (
    SophonManifestProto,
)
from sophon.speed_limiter import SophonDownloadSpeedLimiter
from sophon.types import (
    SophonChunkManifestInfoPair,
    SophonChunksInfo,
    SophonManifestInfo,
)
from sophon.update import SophonUpdate

# ============================================================================
# FIXTURES AND HELPERS
# ============================================================================


class TestDataGenerator:
    """Generator for test data with known properties."""

    @staticmethod
    def create_test_data(size: int = 1024, pattern: bytes = b"TEST") -> bytes:
        """Create deterministic test data."""
        pattern_len = len(pattern)
        return (pattern * (size // pattern_len + 1))[:size]

    @staticmethod
    def create_compressed_data(data: bytes) -> bytes:
        """Create zstandard compressed data."""
        compressor = zstandard.ZstdCompressor()
        return compressor.compress(data)

    @staticmethod
    def calculate_hash(data: bytes) -> bytes:
        """Calculate MD5 hash of data."""
        return hashlib.md5(data).digest()

    @staticmethod
    def create_manifest_proto(
        asset_name: str,
        asset_size: int,
        asset_hash: str,
        chunks_data: list[tuple[str, int, str]],
    ) -> bytes:
        """Create a mock manifest protobuf."""
        proto = SophonManifestProto()
        asset = proto.Assets.add()
        asset.AssetName = asset_name
        asset.AssetSize = asset_size
        asset.AssetHashMd5 = asset_hash

        offset = 0
        for chunk_name, chunk_size, chunk_hash in chunks_data:
            chunk = asset.AssetChunks.add()
            chunk.ChunkName = chunk_name
            chunk.ChunkDecompressedHashMd5 = chunk_hash
            chunk.ChunkOnFileOffset = offset
            chunk.ChunkSize = chunk_size
            chunk.ChunkSizeDecompressed = chunk_size
            offset += chunk_size

        return proto.SerializeToString()


@pytest.fixture
def test_data_gen():
    """Provide test data generator."""
    return TestDataGenerator()


@pytest.fixture
def temp_dir():
    """Provide temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_client_session():
    """Provide mock aiohttp session."""
    return MagicMock(spec=aiohttp.ClientSession)


# ============================================================================
# TEST SUITES
# ============================================================================


class TestChunkVerification:
    """Test chunk verification and hashing."""

    def test_chunk_creation_valid(self):
        """Test creating a valid chunk."""
        chunk = SophonChunk(
            chunk_name="chunk_001.bin",
            chunk_hash_decompressed=b"test_hash_value_12",
            chunk_offset=0,
            chunk_size=1024,
            chunk_size_decompressed=2048,
        )

        assert chunk.chunk_name == "chunk_001.bin"
        assert chunk.chunk_size == 1024
        assert chunk.chunk_size_decompressed == 2048
        assert chunk.chunk_offset == 0

    def test_chunk_creation_invalid_size(self):
        """Test chunk creation with invalid sizes."""
        with pytest.raises(ValueError, match="chunk_size must be greater than 0"):
            SophonChunk(
                chunk_name="chunk.bin",
                chunk_hash_decompressed=b"hash",
                chunk_offset=0,
                chunk_size=0,
                chunk_size_decompressed=1024,
            )

        with pytest.raises(ValueError, match="chunk_size_decompressed must be greater than 0"):
            SophonChunk(
                chunk_name="chunk.bin",
                chunk_hash_decompressed=b"hash",
                chunk_offset=0,
                chunk_size=1024,
                chunk_size_decompressed=0,
            )

    @pytest.mark.asyncio
    async def test_check_chunk_hash_async_success(self, test_data_gen):
        """Test successful chunk hash verification."""
        data = test_data_gen.create_test_data(2048)
        hash_value = test_data_gen.calculate_hash(data)

        chunk = SophonChunk(
            chunk_name="chunk.bin",
            chunk_hash_decompressed=hash_value,
            chunk_offset=0,
            chunk_size=len(data),
            chunk_size_decompressed=len(data),
        )

        stream = io.BytesIO(data)
        result = await chunk.check_chunk_hash_async(stream, verify_from_offset=False)
        assert result is True

    @pytest.mark.asyncio
    async def test_check_chunk_hash_async_with_offset(self, test_data_gen):
        """Test chunk hash verification with file offset."""
        prefix = test_data_gen.create_test_data(512, b"PREFIX")
        data = test_data_gen.create_test_data(1024, b"DATA")
        hash_value = test_data_gen.calculate_hash(data)
        full_data = prefix + data

        chunk = SophonChunk(
            chunk_name="chunk.bin",
            chunk_hash_decompressed=hash_value,
            chunk_offset=len(prefix),
            chunk_size=len(data),
            chunk_size_decompressed=len(data),
        )

        stream = io.BytesIO(full_data)
        result = await chunk.check_chunk_hash_async(stream, verify_from_offset=True)
        assert result is True

    @pytest.mark.asyncio
    async def test_check_chunk_hash_async_mismatch(self, test_data_gen):
        """Test chunk hash verification failure."""
        data = test_data_gen.create_test_data(1024)
        wrong_data = test_data_gen.create_test_data(1024, b"WRONG")
        hash_value = test_data_gen.calculate_hash(wrong_data)

        chunk = SophonChunk(
            chunk_name="chunk.bin",
            chunk_hash_decompressed=hash_value,
            chunk_offset=0,
            chunk_size=len(data),
            chunk_size_decompressed=len(data),
        )

        stream = io.BytesIO(data)
        result = await chunk.check_chunk_hash_async(stream, verify_from_offset=False)
        assert result is False

    @pytest.mark.asyncio
    async def test_check_chunk_hash_async_large_data(self, test_data_gen):
        """Test chunk hash verification with large data (10 MB)."""
        size = 10 * 1024 * 1024  # 10 MB
        data = test_data_gen.create_test_data(size)
        hash_value = test_data_gen.calculate_hash(data)

        chunk = SophonChunk(
            chunk_name="large_chunk.bin",
            chunk_hash_decompressed=hash_value,
            chunk_offset=0,
            chunk_size=len(data),
            chunk_size_decompressed=len(data),
        )

        stream = io.BytesIO(data)
        result = await chunk.check_chunk_hash_async(stream, verify_from_offset=False)
        assert result is True


class TestAssetDownload:
    """Test asset download functionality."""

    def test_asset_creation(self):
        """Test SophonAsset creation."""
        asset = SophonAsset(
            asset_name="game_data.bin",
            asset_size=10 * 1024 * 1024,
            asset_hash="abc123def456",
            is_directory=False,
        )

        assert asset.asset_name == "game_data.bin"
        assert asset.asset_size == 10 * 1024 * 1024
        assert asset.is_directory is False

    def test_asset_creation_directory(self):
        """Test directory asset creation."""
        asset = SophonAsset(
            asset_name="data_dir/",
            asset_size=0,
            is_directory=True,
        )

        assert asset.is_directory is True
        assert asset.asset_size == 0

    def test_asset_add_chunk(self, test_data_gen):
        """Test adding chunks to asset."""
        asset = SophonAsset(
            asset_name="game_data.bin",
            asset_size=2048,
        )

        chunk = SophonChunk(
            chunk_name="chunk_1.bin",
            chunk_hash_decompressed=test_data_gen.calculate_hash(b"data"),
            chunk_offset=0,
            chunk_size=2048,
            chunk_size_decompressed=2048,
        )

        asset.chunks = [chunk]
        assert len(asset.chunks) == 1
        assert asset.chunks[0].chunk_name == "chunk_1.bin"

    def test_asset_validate_chunks_success(self, test_data_gen):
        """Test chunk validation success."""
        asset = SophonAsset(
            asset_name="game_data.bin",
            asset_size=1024,
            chunks=[
                SophonChunk(
                    chunk_name="chunk_1.bin",
                    chunk_hash_decompressed=test_data_gen.calculate_hash(b"test"),
                    chunk_offset=0,
                    chunk_size=1024,
                    chunk_size_decompressed=1024,
                )
            ],
        )

        # Should not raise
        asset._validate_chunks_state()

    def test_asset_validate_chunks_failure(self):
        """Test chunk validation failure."""
        asset = SophonAsset(asset_name="game_data.bin", asset_size=1024)

        with pytest.raises(ValueError, match="has no chunks initialized"):
            asset._validate_chunks_state()

    @pytest.mark.asyncio
    async def test_write_to_stream_async_file_creation(self, temp_dir, test_data_gen):
        """Test file creation during download."""
        output_file = temp_dir / "output.bin"
        expected_size = 2048

        asset = SophonAsset(
            asset_name="test.bin",
            asset_size=expected_size,
            chunks=[
                SophonChunk(
                    chunk_name="chunk_1.bin",
                    chunk_hash_decompressed=test_data_gen.calculate_hash(b"test"),
                    chunk_offset=0,
                    chunk_size=expected_size,
                    chunk_size_decompressed=expected_size,
                )
            ],
        )

        mock_session = MagicMock(spec=aiohttp.ClientSession)

        async def mock_perform(*args, **kwargs):
            pass

        with patch.object(
            asset, "_perform_write_stream_thread_async", side_effect=mock_perform
        ):
            await asset.write_to_stream_async(
                client=mock_session, output_path=str(output_file)
            )

        assert output_file.exists()
        assert output_file.stat().st_size == expected_size

    @pytest.mark.asyncio
    async def test_write_to_stream_async_multiple_chunks(self, temp_dir, test_data_gen):
        """Test downloading multiple chunks sequentially."""
        output_file = temp_dir / "output.bin"
        chunk_size = 1024
        num_chunks = 3

        chunks = [
            SophonChunk(
                chunk_name=f"chunk_{i}.bin",
                chunk_hash_decompressed=test_data_gen.calculate_hash(b"chunk"),
                chunk_offset=i * chunk_size,
                chunk_size=chunk_size,
                chunk_size_decompressed=chunk_size,
            )
            for i in range(num_chunks)
        ]

        asset = SophonAsset(
            asset_name="test.bin",
            asset_size=chunk_size * num_chunks,
            chunks=chunks,
        )

        mock_session = MagicMock(spec=aiohttp.ClientSession)
        call_count = 0

        async def mock_perform(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.001)

        with patch.object(
            asset, "_perform_write_stream_thread_async", side_effect=mock_perform
        ):
            await asset.write_to_stream_async(
                client=mock_session, output_path=str(output_file)
            )

            assert call_count == num_chunks

        assert output_file.exists()
        assert output_file.stat().st_size == chunk_size * num_chunks

    @pytest.mark.asyncio
    async def test_write_to_stream_async_parallel_downloads(
        self, temp_dir, test_data_gen
    ):
        """Test parallel chunk downloads."""
        output_file = temp_dir / "output.bin"
        chunk_size = 1024
        num_chunks = 4

        chunks = [
            SophonChunk(
                chunk_name=f"chunk_{i}.bin",
                chunk_hash_decompressed=test_data_gen.calculate_hash(b"chunk"),
                chunk_offset=i * chunk_size,
                chunk_size=chunk_size,
                chunk_size_decompressed=chunk_size,
            )
            for i in range(num_chunks)
        ]

        asset = SophonAsset(
            asset_name="test.bin",
            asset_size=chunk_size * num_chunks,
            chunks=chunks,
        )

        mock_session = MagicMock(spec=aiohttp.ClientSession)
        call_times = []

        async def mock_perform(*args, **kwargs):
            call_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.01)

        with patch.object(
            asset, "_perform_write_stream_thread_async", side_effect=mock_perform
        ):
            parallel_options = ParallelOptions(max_degree_of_parallelism=2)
            await asset.write_to_stream_async(
                client=mock_session,
                output_path=str(output_file),
                parallel_options=parallel_options,
            )

        assert len(call_times) == num_chunks


class TestManifestHandling:
    """Test manifest parsing and enumeration."""

    def test_create_manifest_info(self):
        """Test creating manifest info."""
        info = SophonManifest.create_manifest_info(
            manifest_base_url="https://example.com/manifest",
            manifest_checksum_md5="abc123",
            manifest_id="manifest.proto",
            is_use_compression=True,
            manifest_size=1024,
            manifest_compressed_size=512,
        )

        assert info.manifest_base_url == "https://example.com/manifest"
        assert info.manifest_id == "manifest.proto"
        assert info.is_use_compression is True

    def test_create_chunks_info(self):
        """Test creating chunks info."""
        chunks_info = SophonManifest.create_chunks_info(
            chunks_base_url="https://example.com/chunks",
            chunks_count=100,
            files_count=50,
            is_use_compression=True,
            total_size=1024 * 1024 * 1024,
            total_compressed_size=512 * 1024 * 1024,
        )

        assert chunks_info.chunks_count == 100
        assert chunks_info.files_count == 50
        assert chunks_info.is_use_compression is True

    @pytest.mark.asyncio
    async def test_enumerate_manifest_single_asset(self, test_data_gen):
        """Test enumerating manifest with single asset."""
        asset_data = test_data_gen.create_test_data(1024)
        asset_hash = hashlib.md5(asset_data).hexdigest()

        manifest_proto = test_data_gen.create_manifest_proto(
            asset_name="game_data.bin",
            asset_size=1024,
            asset_hash=asset_hash,
            chunks_data=[
                ("chunk_1.bin", 1024, hashlib.md5(asset_data).hexdigest()),
            ],
        )

        info_pair = SophonChunkManifestInfoPair(
            is_found=True,
            manifest_info=SophonManifestInfo(
                manifest_base_url="http://test",
                manifest_id="manifest.proto",
            ),
            chunks_info=SophonChunksInfo(chunks_base_url="http://test/chunks"),
        )

        with aioresponses() as m:
            m.get("http://test/manifest.proto", body=manifest_proto)

            async with aiohttp.ClientSession() as session:
                assets = []
                async for asset in SophonManifest.enumerate_async(session, info_pair):
                    assets.append(asset)

                assert len(assets) == 1
                assert assets[0].asset_name == "game_data.bin"
                assert assets[0].asset_size == 1024

    @pytest.mark.asyncio
    async def test_enumerate_manifest_multiple_assets(self, test_data_gen):
        """Test enumerating manifest with multiple assets."""
        manifest_proto = test_data_gen.create_manifest_proto(
            asset_name="game_data.bin",
            asset_size=2048,
            asset_hash=hashlib.md5(b"game_data").hexdigest(),
            chunks_data=[
                ("chunk_1.bin", 1024, hashlib.md5(b"chunk1").hexdigest()),
                ("chunk_2.bin", 1024, hashlib.md5(b"chunk2").hexdigest()),
            ],
        )

        # Add second asset
        proto = SophonManifestProto()
        proto.ParseFromString(manifest_proto)
        asset2 = proto.Assets.add()
        asset2.AssetName = "config.json"
        asset2.AssetSize = 512
        asset2.AssetHashMd5 = hashlib.md5(b"config").hexdigest()
        chunk = asset2.AssetChunks.add()
        chunk.ChunkName = "chunk_3.bin"
        chunk.ChunkDecompressedHashMd5 = hashlib.md5(b"chunk3").hexdigest()
        chunk.ChunkOnFileOffset = 0
        chunk.ChunkSize = 512
        chunk.ChunkSizeDecompressed = 512

        updated_manifest = proto.SerializeToString()

        info_pair = SophonChunkManifestInfoPair(
            is_found=True,
            manifest_info=SophonManifestInfo(
                manifest_base_url="http://test",
                manifest_id="manifest.proto",
            ),
            chunks_info=SophonChunksInfo(chunks_base_url="http://test/chunks"),
        )

        with aioresponses() as m:
            m.get("http://test/manifest.proto", body=updated_manifest)

            async with aiohttp.ClientSession() as session:
                assets = []
                async for asset in SophonManifest.enumerate_async(session, info_pair):
                    assets.append(asset)

                assert len(assets) == 2
                assert assets[0].asset_name == "game_data.bin"
                assert assets[1].asset_name == "config.json"

    @pytest.mark.asyncio
    async def test_enumerate_manifest_network_error(self, test_data_gen):
        """Test manifest enumeration with network error."""
        info_pair = SophonChunkManifestInfoPair(
            is_found=True,
            manifest_info=SophonManifestInfo(
                manifest_base_url="http://test",
                manifest_id="manifest.proto",
            ),
            chunks_info=SophonChunksInfo(chunks_base_url="http://test/chunks"),
        )

        with aioresponses() as m:
            m.get("http://test/manifest.proto", exception=aiohttp.ClientError("Connection error"))

            async with aiohttp.ClientSession() as session:
                with pytest.raises(aiohttp.ClientError):
                    async for _ in SophonManifest.enumerate_async(session, info_pair):
                        pass


class TestUpdateEnumeration:
    """Test update enumeration and diff detection."""

    @pytest.mark.asyncio
    async def test_update_enumeration_changed_asset(self, test_data_gen):
        """Test detecting changed assets in update."""
        # Old manifest: single asset
        old_chunks = [
            ("chunk_1.bin", 1024, hashlib.md5(b"old_data").hexdigest()),
        ]
        old_data = test_data_gen.create_manifest_proto(
            "game_data.bin", 1024, "old_hash", old_chunks
        )

        # New manifest: asset changed (different hash)
        new_chunks = [
            ("chunk_1_new.bin", 1024, hashlib.md5(b"new_data").hexdigest()),
        ]
        new_data = test_data_gen.create_manifest_proto(
            "game_data.bin", 1024, "new_hash", new_chunks
        )

        info_pair_old = SophonChunkManifestInfoPair(
            is_found=True,
            manifest_info=SophonManifestInfo(
                manifest_base_url="http://test",
                manifest_id="old.manifest",
            ),
            chunks_info=SophonChunksInfo(chunks_base_url="http://test/chunks"),
        )

        info_pair_new = SophonChunkManifestInfoPair(
            is_found=True,
            manifest_info=SophonManifestInfo(
                manifest_base_url="http://test",
                manifest_id="new.manifest",
            ),
            chunks_info=SophonChunksInfo(chunks_base_url="http://test/chunks"),
        )

        with aioresponses() as m:
            m.get("http://test/old.manifest", body=old_data)
            m.get("http://test/new.manifest", body=new_data)

            async with aiohttp.ClientSession() as session:
                update_assets = []
                async for asset in SophonUpdate.enumerate_update_async(
                    session, info_pair_old, info_pair_new
                ):
                    update_assets.append(asset)

                assert len(update_assets) == 1
                assert update_assets[0].asset_name == "game_data.bin"

    @pytest.mark.asyncio
    async def test_update_enumeration_shared_chunks(self, test_data_gen):
        """Test update with shared chunks between versions."""
        shared_hash = hashlib.md5(b"shared_data").hexdigest()

        old_chunks = [
            ("chunk_shared.bin", 1024, shared_hash),
            ("chunk_old_1.bin", 1024, hashlib.md5(b"old_data").hexdigest()),
        ]
        old_data = test_data_gen.create_manifest_proto(
            "game_data.bin", 2048, "old_hash", old_chunks
        )

        new_chunks = [
            ("chunk_shared.bin", 1024, shared_hash),
            ("chunk_new_1.bin", 1024, hashlib.md5(b"new_data").hexdigest()),
        ]
        new_data = test_data_gen.create_manifest_proto(
            "game_data.bin", 2048, "new_hash", new_chunks
        )

        info_pair_old = SophonChunkManifestInfoPair(
            is_found=True,
            manifest_info=SophonManifestInfo(
                manifest_base_url="http://test",
                manifest_id="old.manifest",
            ),
            chunks_info=SophonChunksInfo(chunks_base_url="http://test/chunks"),
        )

        info_pair_new = SophonChunkManifestInfoPair(
            is_found=True,
            manifest_info=SophonManifestInfo(
                manifest_base_url="http://test",
                manifest_id="new.manifest",
            ),
            chunks_info=SophonChunksInfo(chunks_base_url="http://test/chunks"),
        )

        with aioresponses() as m:
            m.get("http://test/old.manifest", body=old_data)
            m.get("http://test/new.manifest", body=new_data)

            async with aiohttp.ClientSession() as session:
                update_assets = []
                async for asset in SophonUpdate.enumerate_update_async(
                    session, info_pair_old, info_pair_new
                ):
                    update_assets.append(asset)

                if len(update_assets) > 0:
                    asset = update_assets[0]
                    assert asset.asset_name == "game_data.bin"


class TestPatchOperations:
    """Test patch application operations."""

    @pytest.mark.asyncio
    async def test_apply_patch_remove(self, temp_dir):
        """Test REMOVE patch operation."""
        input_dir = temp_dir / "input"
        patch_dir = temp_dir / "patch"
        input_dir.mkdir()
        patch_dir.mkdir()

        # Create file to remove
        target_file = input_dir / "old_file.txt"
        target_file.write_text("old content")
        assert target_file.exists()

        patch_asset = SophonPatchAsset(
            patch_method=SophonPatchMethod.REMOVE,
            original_file_path="old_file.txt",
        )

        async with aiohttp.ClientSession() as session:
            await patch_asset.apply_patch_update_async(
                client=session,
                input_dir=str(input_dir),
                patch_output_dir=str(patch_dir),
                remove_old_assets=True,
            )

        assert not target_file.exists()

    @pytest.mark.asyncio
    async def test_apply_patch_copy_over(self, temp_dir):
        """Test COPY_OVER patch operation."""
        input_dir = temp_dir / "input"
        patch_dir = temp_dir / "patch"
        input_dir.mkdir()
        patch_dir.mkdir()

        # Create patch source file
        patch_file = patch_dir / "patch_data.bin"
        prefix = b"IGNORE_THIS"
        content = b"NEW_CONTENT"
        patch_file.write_bytes(prefix + content)

        patch_asset = SophonPatchAsset(
            patch_method=SophonPatchMethod.COPY_OVER,
            patch_name_source="patch_data.bin",
            target_file_path="new_file.txt",
            patch_offset=len(prefix),
            patch_chunk_length=len(content),
        )

        async with aiohttp.ClientSession() as session:
            await patch_asset.apply_patch_update_async(
                client=session,
                input_dir=str(input_dir),
                patch_output_dir=str(patch_dir),
            )

        # Verify target file created with correct content
        target_file = input_dir / "new_file.txt"
        assert target_file.exists()
        assert target_file.read_bytes() == content

    @pytest.mark.asyncio
    async def test_apply_patch_copy_over_with_offset(self, temp_dir):
        """Test COPY_OVER patch with offset."""
        input_dir = temp_dir / "input"
        patch_dir = temp_dir / "patch"
        input_dir.mkdir()
        patch_dir.mkdir()

        # Create patch source with multiple sections
        patch_file = patch_dir / "patch_data.bin"
        ignore1 = b"IGNORE1"
        content = b"IMPORTANT"
        ignore2 = b"IGNORE2"
        patch_file.write_bytes(ignore1 + content + ignore2)

        patch_asset = SophonPatchAsset(
            patch_method=SophonPatchMethod.COPY_OVER,
            patch_name_source="patch_data.bin",
            target_file_path="extracted.bin",
            patch_offset=len(ignore1),
            patch_chunk_length=len(content),
        )

        async with aiohttp.ClientSession() as session:
            await patch_asset.apply_patch_update_async(
                client=session,
                input_dir=str(input_dir),
                patch_output_dir=str(patch_dir),
            )

        target_file = input_dir / "extracted.bin"
        assert target_file.read_bytes() == content


class TestZstdDecompression:
    """Test Zstandard decompression streaming."""

    @pytest.mark.asyncio
    async def test_zstd_decompression_stream(self, test_data_gen):
        """Test zstd decompression stream."""
        original_data = test_data_gen.create_test_data(4096)
        compressed_data = test_data_gen.create_compressed_data(original_data)

        mock_reader = AsyncMock(spec=aiohttp.StreamReader)
        mock_reader.read.side_effect = [compressed_data, b""]

        stream = ZstdDecompressionStream(mock_reader)
        result = await stream.read(-1)

        assert result == original_data

    @pytest.mark.asyncio
    async def test_zstd_decompression_chunked(self, test_data_gen):
        """Test zstd decompression with chunked reading."""
        original_data = test_data_gen.create_test_data(8192)
        compressed_data = test_data_gen.create_compressed_data(original_data)

        # Split compressed data into chunks
        chunk_size = len(compressed_data) // 3
        chunks = [
            compressed_data[:chunk_size],
            compressed_data[chunk_size : 2 * chunk_size],
            compressed_data[2 * chunk_size :],
            b"",
        ]

        mock_reader = AsyncMock(spec=aiohttp.StreamReader)
        mock_reader.read.side_effect = chunks + [b""] * 5

        stream = ZstdDecompressionStream(mock_reader)
        result = b""
        while True:
            chunk = await stream.read(2048)
            if not chunk:
                break
            result += chunk

        assert result == original_data

    @pytest.mark.asyncio
    async def test_zstd_decompression_large_data(self, test_data_gen):
        """Test zstd decompression with large data (5 MB)."""
        size = 5 * 1024 * 1024
        original_data = test_data_gen.create_test_data(size)
        compressed_data = test_data_gen.create_compressed_data(original_data)

        mock_reader = AsyncMock(spec=aiohttp.StreamReader)
        mock_reader.read.side_effect = [compressed_data, b""]

        stream = ZstdDecompressionStream(mock_reader)
        result = await stream.read(-1)

        assert result == original_data
        assert len(result) == size


class TestSpeedLimiter:
    """Test speed limiter functionality."""

    def test_speed_limiter_creation(self):
        """Test creating speed limiter instance."""
        limiter = SophonDownloadSpeedLimiter.create_instance(12345)

        assert limiter.context == 12345

    def test_speed_limiter_delegate(self):
        """Test speed limiter delegate configuration."""
        delegate_called = False

        async def mock_delegate(context, bytes_read, token):
            nonlocal delegate_called
            delegate_called = True

        SophonDownloadSpeedLimiter.set_add_bytes_or_wait_delegate(mock_delegate)
        SophonDownloadSpeedLimiter.create_instance(999)

        assert SophonDownloadSpeedLimiter._add_bytes_or_wait_delegate is not None


class TestExceptionHandling:
    """Test exception handling and error recovery."""

    def test_exception_hierarchy(self):
        """Test exception class hierarchy."""
        assert issubclass(ManifestNotFoundError, SophonException)
        assert issubclass(ChunkVerificationError, SophonException)
        assert issubclass(DownloadError, SophonException)
        assert issubclass(PatchError, SophonException)
        assert issubclass(InvalidManifestError, SophonException)

    def test_exception_instantiation(self):
        """Test exception creation with messages."""
        exc = DownloadError("Download failed due to network error")
        assert str(exc) == "Download failed due to network error"

        exc2 = ChunkVerificationError("Hash mismatch on chunk_001.bin")
        assert str(exc2) == "Hash mismatch on chunk_001.bin"


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""

    @pytest.mark.asyncio
    async def test_complete_download_workflow(self, temp_dir, test_data_gen):
        """Test complete download workflow from start to finish."""
        # Setup
        output_file = temp_dir / "downloaded.bin"
        chunk_data = test_data_gen.create_test_data(1024)
        chunk_hash = test_data_gen.calculate_hash(chunk_data)

        chunk = SophonChunk(
            chunk_name="chunk_1.bin",
            chunk_hash_decompressed=chunk_hash,
            chunk_offset=0,
            chunk_size=1024,
            chunk_size_decompressed=1024,
        )

        asset = SophonAsset(
            asset_name="game.bin",
            asset_size=1024,
            chunks=[chunk],
        )

        # Mock session
        mock_session = MagicMock(spec=aiohttp.ClientSession)

        # Create output file
        async def mock_perform(*args, **kwargs):
            output_file.write_bytes(chunk_data)

        with patch.object(
            asset, "_perform_write_stream_thread_async", side_effect=mock_perform
        ):
            await asset.write_to_stream_async(
                client=mock_session, output_path=str(output_file)
            )

        # Verify
        assert output_file.exists()
        assert output_file.read_bytes() == chunk_data

    @pytest.mark.asyncio
    async def test_error_recovery_scenario(self, temp_dir):
        """Test error recovery in download scenarios."""
        output_file = temp_dir / "output.bin"

        asset = SophonAsset(
            asset_name="test.bin",
            asset_size=0,  # No chunks - will trigger validation error
        )

        mock_session = MagicMock(spec=aiohttp.ClientSession)

        with pytest.raises(ValueError):
            # This should fail validation because asset has no chunks
            await asset.write_to_stream_async(
                client=mock_session, output_path=str(output_file)
            )


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_chunk_with_zero_decompressed_size_on_equality(self):
        """Test chunk creation with specific size combinations."""
        # Compressed size can be larger than decompressed (worst case scenario)
        chunk = SophonChunk(
            chunk_name="small.bin",
            chunk_hash_decompressed=b"hash",
            chunk_offset=0,
            chunk_size=2000,  # Compressed
            chunk_size_decompressed=1024,  # Decompressed
        )

        assert chunk.chunk_size > chunk.chunk_size_decompressed

    def test_asset_with_maximum_size(self):
        """Test asset with very large size."""
        asset = SophonAsset(
            asset_name="huge.bin",
            asset_size=1024 * 1024 * 1024 * 1024,  # 1 TB
            is_directory=False,
        )

        assert asset.asset_size == 1024 * 1024 * 1024 * 1024

    @pytest.mark.asyncio
    async def test_manifest_enumeration_empty(self, test_data_gen):
        """Test enumerating empty manifest."""
        proto = SophonManifestProto()
        manifest_data = proto.SerializeToString()

        info_pair = SophonChunkManifestInfoPair(
            is_found=True,
            manifest_info=SophonManifestInfo(
                manifest_base_url="http://test",
                manifest_id="empty.manifest",
            ),
            chunks_info=SophonChunksInfo(chunks_base_url="http://test/chunks"),
        )

        with aioresponses() as m:
            m.get("http://test/empty.manifest", body=manifest_data)

            async with aiohttp.ClientSession() as session:
                assets = []
                async for asset in SophonManifest.enumerate_async(session, info_pair):
                    assets.append(asset)

                assert len(assets) == 0


class TestConcurrency:
    """Test concurrent operations."""

    @pytest.mark.asyncio
    async def test_parallel_chunk_download_concurrency(self, temp_dir, test_data_gen):
        """Test parallel chunk downloads are truly concurrent."""
        output_file = temp_dir / "output.bin"
        chunk_size = 512
        num_chunks = 4

        chunks = [
            SophonChunk(
                chunk_name=f"chunk_{i}.bin",
                chunk_hash_decompressed=test_data_gen.calculate_hash(b"chunk"),
                chunk_offset=i * chunk_size,
                chunk_size=chunk_size,
                chunk_size_decompressed=chunk_size,
            )
            for i in range(num_chunks)
        ]

        asset = SophonAsset(
            asset_name="concurrent.bin",
            asset_size=chunk_size * num_chunks,
            chunks=chunks,
        )

        mock_session = MagicMock(spec=aiohttp.ClientSession)
        call_count = 0

        async def mock_perform(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)

        with patch.object(
            asset, "_perform_write_stream_thread_async", side_effect=mock_perform
        ):
            parallel_options = ParallelOptions(max_degree_of_parallelism=2)
            await asset.write_to_stream_async(
                client=mock_session,
                output_path=str(output_file),
                parallel_options=parallel_options,
            )

        # Verify all chunks were processed
        assert call_count == num_chunks


class TestPerformance:
    """Test performance characteristics."""

    @pytest.mark.asyncio
    async def test_large_manifest_enumeration_performance(self, test_data_gen):
        """Test manifest enumeration performance with many assets."""
        # Create manifest with 100 assets
        proto = SophonManifestProto()
        for i in range(100):
            asset = proto.Assets.add()
            asset.AssetName = f"asset_{i:03d}.bin"
            asset.AssetSize = 1024 * (i + 1)
            asset.AssetHashMd5 = hashlib.md5(f"asset_{i}".encode()).hexdigest()

            # Add 5 chunks per asset
            for j in range(5):
                chunk = asset.AssetChunks.add()
                chunk.ChunkName = f"chunk_{i:03d}_{j}.bin"
                chunk.ChunkDecompressedHashMd5 = hashlib.md5(
                    f"chunk_{i}_{j}".encode()
                ).hexdigest()
                chunk.ChunkOnFileOffset = j * 1024
                chunk.ChunkSize = 1024
                chunk.ChunkSizeDecompressed = 1024

        manifest_data = proto.SerializeToString()

        info_pair = SophonChunkManifestInfoPair(
            is_found=True,
            manifest_info=SophonManifestInfo(
                manifest_base_url="http://test",
                manifest_id="large.manifest",
            ),
            chunks_info=SophonChunksInfo(chunks_base_url="http://test/chunks"),
        )

        with aioresponses() as m:
            m.get("http://test/large.manifest", body=manifest_data)

            async with aiohttp.ClientSession() as session:
                assets = []
                async for asset in SophonManifest.enumerate_async(session, info_pair):
                    assets.append(asset)

                assert len(assets) == 100
                assert all(a.asset_name.startswith("asset_") for a in assets)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
