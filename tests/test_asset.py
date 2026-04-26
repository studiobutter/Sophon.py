import asyncio
import os
import pytest
from unittest.mock import MagicMock, patch

import aiohttp
from sophon.asset import SophonAsset, SourceStreamType
from sophon.chunk import SophonChunk, ParallelOptions
from sophon.exceptions import DownloadError
from sophon.types.chunks_info import SophonChunksInfo


class TestSophonAssetCore:
    """Test cases for core SophonAsset logic."""

    def test_validate_chunks_state_success(self):
        """Test validation passes when chunks exist."""
        asset = SophonAsset(
            asset_name="test.bin",
            asset_size=1024,
            chunks=[
                SophonChunk(
                    chunk_name="chunk1",
                    chunk_hash_decompressed=b"hash",
                    chunk_offset=0,
                    chunk_size=1024,
                    chunk_size_decompressed=1024,
                )
            ]
        )
        # Should not raise
        asset._validate_chunks_state()

    def test_validate_chunks_state_failure(self):
        """Test validation fails when no chunks."""
        asset = SophonAsset(asset_name="test.bin", asset_size=1024)
        with pytest.raises(ValueError, match="has no chunks initialized"):
            asset._validate_chunks_state()

    @pytest.mark.asyncio
    async def test_write_to_stream_async_creates_file(self, tmp_path):
        """Test write_to_stream_async creates and truncates file."""
        output_file = tmp_path / "output.bin"
        asset = SophonAsset(
            asset_name="test.bin",
            asset_size=2048,
            chunks=[
                SophonChunk(
                    chunk_name="chunk1",
                    chunk_hash_decompressed=b"hash",
                    chunk_offset=0,
                    chunk_size=1024,
                    chunk_size_decompressed=1024,
                )
            ]
        )

        mock_session = MagicMock(spec=aiohttp.ClientSession)
        
        # Patch the inner download method to do nothing so we only test file creation
        with patch.object(asset, "_perform_write_stream_thread_async", new_callable=MagicMock) as mock_perform:
            # We need an async mock
            async def mock_async(*args, **kwargs):
                pass
            mock_perform.side_effect = mock_async

            await asset.write_to_stream_async(
                client=mock_session,
                output_path=str(output_file)
            )

        assert output_file.exists()
        assert output_file.stat().st_size == 2048

    @pytest.mark.asyncio
    async def test_write_to_stream_async_parallel_calls(self, tmp_path):
        """Test write_to_stream_async calls chunks in parallel."""
        output_file = tmp_path / "output.bin"
        asset = SophonAsset(
            asset_name="test.bin",
            asset_size=2048,
            chunks=[
                SophonChunk(
                    chunk_name="chunk1",
                    chunk_hash_decompressed=b"hash1",
                    chunk_offset=0,
                    chunk_size=1024,
                    chunk_size_decompressed=1024,
                ),
                SophonChunk(
                    chunk_name="chunk2",
                    chunk_hash_decompressed=b"hash2",
                    chunk_offset=1024,
                    chunk_size=1024,
                    chunk_size_decompressed=1024,
                )
            ]
        )

        mock_session = MagicMock(spec=aiohttp.ClientSession)
        call_count = 0
        
        async def mock_perform(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)

        with patch.object(asset, "_perform_write_stream_thread_async", side_effect=mock_perform) as mock_method:
            opts = ParallelOptions(max_degree_of_parallelism=2)
            await asset.write_to_stream_async(
                client=mock_session,
                output_path=str(output_file),
                parallel_options=opts
            )

            assert mock_method.call_count == 2
            assert call_count == 2