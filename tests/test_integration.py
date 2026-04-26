import asyncio
import aiohttp
import pytest
from aioresponses import aioresponses
from sophon.manifest import SophonManifest
from sophon.update import SophonUpdate
from sophon.proto.SophonManifestProto_pb2 import SophonManifestProto, SophonManifestAssetProperty, SophonManifestAssetChunk
from sophon.types import SophonChunkManifestInfoPair, SophonManifestInfo, SophonChunksInfo

def create_mock_manifest_data(asset_name, asset_hash, chunks_data):
    proto = SophonManifestProto()
    asset = proto.Assets.add()
    asset.AssetName = asset_name
    asset.AssetSize = sum(c[1] for c in chunks_data)
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

class TestIntegration:
    @pytest.mark.asyncio
    async def test_update_enumeration(self):
        # We will simulate old and new manifests
        old_chunks = [
            ("chunk_old_1", 1024, "11112222333344445555666677778888"),
            ("chunk_shared", 1024, "aaaabbbbccccddddeeeeffff00001111"),
        ]
        
        new_chunks = [
            ("chunk_shared", 1024, "aaaabbbbccccddddeeeeffff00001111"),
            ("chunk_new_1", 1024, "99990000111122223333444455556666"),
        ]
        
        old_data = create_mock_manifest_data("game_data.bin", "old_hash", old_chunks)
        new_data = create_mock_manifest_data("game_data.bin", "new_hash", new_chunks)
        
        info_pair_old = SophonChunkManifestInfoPair(
            is_found=True,
            manifest_info=SophonManifestInfo(manifest_base_url="http://test", manifest_id="old.manifest"),
            chunks_info=SophonChunksInfo(chunks_base_url="http://test/chunks")
        )
        
        info_pair_new = SophonChunkManifestInfoPair(
            is_found=True,
            manifest_info=SophonManifestInfo(manifest_base_url="http://test", manifest_id="new.manifest"),
            chunks_info=SophonChunksInfo(chunks_base_url="http://test/chunks")
        )

        with aioresponses() as m:
            m.get('http://test/old.manifest', body=old_data)
            m.get('http://test/new.manifest', body=new_data)
            
            async with aiohttp.ClientSession() as session:
                update_assets = []
                async for asset in SophonUpdate.enumerate_update_async(session, info_pair_old, info_pair_new):
                    update_assets.append(asset)
                    
                # Assertions
                assert len(update_assets) == 1
                asset = update_assets[0]
                assert asset.asset_name == "game_data.bin"
                assert asset.is_has_patch is True
                assert len(asset.chunks) == 2
                
                # Check that chunk mapping was successfully resolved
                chunk_shared = next(c for c in asset.chunks if c.chunk_name == "chunk_shared")
                chunk_new = next(c for c in asset.chunks if c.chunk_name == "chunk_new_1")
                
                # The shared chunk should map back to the old offset!
                assert chunk_shared.chunk_old_offset == 1024  # because in old_chunks, it's the second chunk
                
                # The new chunk should NOT map back to an old offset
                assert chunk_new.chunk_old_offset == -1
