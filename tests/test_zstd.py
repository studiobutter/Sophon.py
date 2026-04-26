import asyncio
import io
import zstandard
import pytest
from unittest.mock import AsyncMock, MagicMock

import aiohttp
from sophon.asset import ZstdDecompressionStream

class TestZstdDecompressionStream:
    @pytest.mark.asyncio
    async def test_decompression(self):
        # Create some compressed data
        data = b"hello world this is a test" * 100
        compressor = zstandard.ZstdCompressor()
        compressed_data = compressor.compress(data)

        # Mock aiohttp.StreamReader
        mock_reader = AsyncMock(spec=aiohttp.StreamReader)
        
        # Simulate reading in two chunks
        split_point = len(compressed_data) // 2
        chunk1 = compressed_data[:split_point]
        chunk2 = compressed_data[split_point:]
        
        mock_reader.read.side_effect = [chunk1, chunk2] + [b""] * 10

        stream = ZstdDecompressionStream(mock_reader)
        
        # Read the decompressed data
        result = b""
        while True:
            chunk = await stream.read(1024)
            if not chunk:
                break
            result += chunk

        assert result == data
        
    @pytest.mark.asyncio
    async def test_read_all(self):
        # Create some compressed data
        data = b"read all test" * 100
        compressor = zstandard.ZstdCompressor()
        compressed_data = compressor.compress(data)

        mock_reader = AsyncMock(spec=aiohttp.StreamReader)
        mock_reader.read.side_effect = [compressed_data, b""]

        stream = ZstdDecompressionStream(mock_reader)
        
        # Read all at once
        result = await stream.read(-1)
        assert result == data
