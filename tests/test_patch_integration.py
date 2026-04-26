import asyncio
import os
import shutil
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
from aioresponses import aioresponses

from sophon.patch import SophonPatchAsset, SophonPatchMethod
from sophon.asset import SophonAsset
from sophon.types import SophonChunksInfo


class TestPatchIntegration:
    @pytest.fixture
    def setup_dirs(self, tmp_path):
        input_dir = tmp_path / "input"
        patch_dir = tmp_path / "patch"
        input_dir.mkdir()
        patch_dir.mkdir()
        return str(input_dir), str(patch_dir)

    @pytest.mark.asyncio
    async def test_apply_patch_remove(self, setup_dirs):
        input_dir, patch_dir = setup_dirs
        target_file = os.path.join(input_dir, "old_file.txt")
        
        with open(target_file, "w") as f:
            f.write("old content")
            
        assert os.path.exists(target_file)
        
        patch_asset = SophonPatchAsset(
            patch_method=SophonPatchMethod.REMOVE,
            original_file_path="old_file.txt"
        )
        
        async with aiohttp.ClientSession() as session:
            await patch_asset.apply_patch_update_async(
                client=session,
                input_dir=input_dir,
                patch_output_dir=patch_dir,
                remove_old_assets=True
            )
            
        assert not os.path.exists(target_file)

    @pytest.mark.asyncio
    async def test_apply_patch_copy_over(self, setup_dirs):
        input_dir, patch_dir = setup_dirs
        patch_source = os.path.join(patch_dir, "patch_data.bin")
        target_file = os.path.join(input_dir, "new_file.txt")
        
        with open(patch_source, "wb") as f:
            f.write(b"IGNORE")
            f.write(b"NEW CONTENT")
            
        patch_asset = SophonPatchAsset(
            patch_method=SophonPatchMethod.COPY_OVER,
            patch_name_source="patch_data.bin",
            target_file_path="new_file.txt",
            patch_offset=6,
            patch_chunk_length=11
        )
        
        async with aiohttp.ClientSession() as session:
            await patch_asset.apply_patch_update_async(
                client=session,
                input_dir=input_dir,
                patch_output_dir=patch_dir
            )
            
        assert os.path.exists(target_file)
        with open(target_file, "rb") as f:
            assert f.read() == b"NEW CONTENT"

    @pytest.mark.asyncio
    async def test_apply_patch_hdiffpatch(self, setup_dirs):
        input_dir, patch_dir = setup_dirs
        original_file = os.path.join(input_dir, "base_file.bin")
        patch_file = os.path.join(patch_dir, "diff.hdiff")
        target_file = os.path.join(input_dir, "patched_file.bin")
        
        with open(original_file, "wb") as f:
            f.write(b"old")
        with open(patch_file, "wb") as f:
            f.write(b"diff")
            
        patch_asset = SophonPatchAsset(
            patch_method=SophonPatchMethod.PATCH,
            original_file_path="base_file.bin",
            patch_name_source="diff.hdiff",
            target_file_path="patched_file.bin"
        )
        
        # Mock asyncio.create_subprocess_exec to pretend hpatchz was successful
        async def mock_subprocess(*args, **kwargs):
            # Create the expected output file to simulate successful patching
            temp_target = kwargs.get('temp_target_path') or args[-1]
            with open(temp_target, "wb") as f:
                f.write(b"patched")
            
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = (b"", b"")
            mock_proc.returncode = 0
            return mock_proc

        with patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess):
            async with aiohttp.ClientSession() as session:
                await patch_asset.apply_patch_update_async(
                    client=session,
                    input_dir=input_dir,
                    patch_output_dir=patch_dir,
                    remove_old_assets=True
                )
                
        assert os.path.exists(target_file)
        with open(target_file, "rb") as f:
            assert f.read() == b"patched"
        assert not os.path.exists(original_file)

    @pytest.mark.asyncio
    async def test_download_patch_async(self, setup_dirs):
        input_dir, patch_dir = setup_dirs
        
        patch_asset = SophonPatchAsset(
            patch_method=SophonPatchMethod.PATCH,
            patch_name_source="patch.hdiff",
            patch_size=10,
            patch_hash="cf3cdcb706c87478c9e39fcef67acb5d",
            patch_info=SophonChunksInfo(chunks_base_url="http://test/chunks")
        )
        
        with aioresponses() as m:
            m.get('http://test/chunks/patch.hdiff', body=b"PATCH_DATA")
            
            async with aiohttp.ClientSession() as session:
                result = await patch_asset.download_patch_async(
                    client=session,
                    input_dir=input_dir,
                    patch_output_dir=patch_dir
                )
                
        assert result is True
        patch_file = os.path.join(patch_dir, "patch.hdiff")
        assert os.path.exists(patch_file)
        with open(patch_file, "rb") as f:
            assert f.read() == b"PATCH_DATA"