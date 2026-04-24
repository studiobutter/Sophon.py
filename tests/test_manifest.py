"""Tests for Sophon manifest functionality."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


class TestSophonManifest:
    """Test cases for SophonManifest."""

    @pytest.mark.asyncio
    async def test_create_manifest_info(self):
        """Test creating manifest info."""
        from sophon.manifest import SophonManifest
        
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

    @pytest.mark.asyncio
    async def test_create_chunks_info(self):
        """Test creating chunks info."""
        from sophon.manifest import SophonManifest
        
        chunks_info = SophonManifest.create_chunks_info(
            chunks_base_url="https://example.com/chunks",
            chunks_count=100,
            files_count=50,
            is_use_compression=True,
            total_size=1024 * 1024 * 1024,  # 1 GB
            total_compressed_size=512 * 1024 * 1024,  # 512 MB
        )
        
        assert chunks_info.chunks_count == 100
        assert chunks_info.files_count == 50
        assert chunks_info.total_size == 1024 * 1024 * 1024


class TestSophonAsset:
    """Test cases for SophonAsset."""

    def test_asset_creation(self):
        """Test creating SophonAsset."""
        from sophon.asset import SophonAsset
        
        asset = SophonAsset(
            asset_name="game_data.bin",
            asset_size=1024 * 1024,
            asset_hash="abc123def456",
            is_directory=False,
        )
        
        assert asset.asset_name == "game_data.bin"
        assert asset.asset_size == 1024 * 1024
        assert asset.is_directory is False

    def test_asset_directory(self):
        """Test creating directory asset."""
        from sophon.asset import SophonAsset
        
        asset = SophonAsset(
            asset_name="data/",
            asset_size=0,
            is_directory=True,
        )
        
        assert asset.is_directory is True
        assert asset.asset_size == 0


if __name__ == "__main__":
    pytest.main([__file__])
