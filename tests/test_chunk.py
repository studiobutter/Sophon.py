import hashlib
import io

import pytest

from sophon.chunk import ParallelOptions, SophonChunk


class TestSophonChunk:
    """Test cases for SophonChunk."""

    def test_chunk_initialization_success(self):
        """Test successful initialization of SophonChunk."""
        chunk = SophonChunk(
            chunk_name="test_chunk.bin",
            chunk_hash_decompressed=b"mock_hash",
            chunk_offset=0,
            chunk_size=1024,
            chunk_size_decompressed=2048,
        )
        assert chunk.chunk_name == "test_chunk.bin"
        assert chunk.chunk_size == 1024
        assert chunk.chunk_size_decompressed == 2048

    def test_chunk_initialization_invalid_sizes(self):
        """Test initialization with invalid sizes."""
        with pytest.raises(ValueError, match="chunk_size must be greater than 0"):
            SophonChunk(
                chunk_name="test_chunk.bin",
                chunk_hash_decompressed=b"mock_hash",
                chunk_offset=0,
                chunk_size=0,
                chunk_size_decompressed=2048,
            )

        with pytest.raises(ValueError, match="chunk_size_decompressed must be greater than 0"):
            SophonChunk(
                chunk_name="test_chunk.bin",
                chunk_hash_decompressed=b"mock_hash",
                chunk_offset=0,
                chunk_size=1024,
                chunk_size_decompressed=0,
            )

    @pytest.mark.asyncio
    async def test_check_chunk_hash_async_success(self):
        """Test hash verification success."""
        data = b"test_data_for_chunk"
        md5 = hashlib.md5(data).digest()

        chunk = SophonChunk(
            chunk_name="test_chunk.bin",
            chunk_hash_decompressed=md5,
            chunk_offset=0,
            chunk_size=len(data),
            chunk_size_decompressed=len(data),
        )

        stream = io.BytesIO(data)
        result = await chunk.check_chunk_hash_async(stream, verify_from_offset=False)
        assert result is True

    @pytest.mark.asyncio
    async def test_check_chunk_hash_async_with_offset(self):
        """Test hash verification with offset."""
        prefix = b"prefix_data"
        data = b"test_data_for_chunk"
        full_data = prefix + data
        md5 = hashlib.md5(data).digest()

        chunk = SophonChunk(
            chunk_name="test_chunk.bin",
            chunk_hash_decompressed=md5,
            chunk_offset=len(prefix),
            chunk_size=len(data),
            chunk_size_decompressed=len(data),
        )

        stream = io.BytesIO(full_data)
        # It should seek to offset and check from there
        result = await chunk.check_chunk_hash_async(stream, verify_from_offset=True)
        assert result is True

    @pytest.mark.asyncio
    async def test_check_chunk_hash_async_failure(self):
        """Test hash verification failure."""
        data = b"test_data_for_chunk"
        wrong_data = b"wrong_data_for_chunk"
        md5 = hashlib.md5(wrong_data).digest()

        chunk = SophonChunk(
            chunk_name="test_chunk.bin",
            chunk_hash_decompressed=md5,
            chunk_offset=0,
            chunk_size=len(data),
            chunk_size_decompressed=len(data),
        )

        stream = io.BytesIO(data)
        result = await chunk.check_chunk_hash_async(stream, verify_from_offset=False)
        assert result is False

class TestParallelOptions:
    """Test cases for ParallelOptions."""

    def test_parallel_options_success(self):
        """Test valid initialization."""
        opts = ParallelOptions(max_degree_of_parallelism=4)
        assert opts.max_degree_of_parallelism == 4

    def test_parallel_options_invalid(self):
        """Test invalid initialization."""
        with pytest.raises(ValueError, match="max_degree_of_parallelism must be at least 1"):
            ParallelOptions(max_degree_of_parallelism=0)
