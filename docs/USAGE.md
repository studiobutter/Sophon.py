# Sophon Usage Guide

This guide demonstrates how to use the Sophon protocol library to download assets, apply updates, and process patches. 

Sophon primarily relies on `aiohttp` for asynchronous HTTP requests and uses `asyncio` for task execution.

## 1. Downloading Assets (Fresh Install)

The most common operation is fetching a game manifest and downloading all its associated assets.

```python
import asyncio
from pathlib import Path
import aiohttp
from sophon import SophonManifest

async def main():
    # 1. Provide the manifest branch URL
    build_url = "https://api-os.hoyoverse.com/launcher_api/v1/manifest"
    output_dir = Path("./game_files")
    output_dir.mkdir(exist_ok=True)

    async with aiohttp.ClientSession() as session:
        # 2. Fetch manifest information
        manifest_pair = await SophonManifest.create_chunk_manifest_info_pair(
            session, build_url, matching_field="game"
        )
        
        if not manifest_pair.is_found:
            print("Manifest not found!")
            return

        # 3. Enumerate assets and download
        async for asset in SophonManifest.enumerate_async(session, manifest_pair):
            if asset.is_directory:
                continue
                
            output_path = output_dir / asset.asset_name
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            print(f"Downloading {asset.asset_name} ({asset.asset_size} bytes)")
            
            # Write chunks to disk
            await asset.write_to_stream_async(
                session, 
                str(output_path),
                # Optional delegates for tracking progress can be passed here
            )

if __name__ == "__main__":
    asyncio.run(main())
```

## 2. Applying Incremental Updates

To apply updates differentially between two known manifest versions (old and new), you can use `SophonUpdate`.

```python
import asyncio
from pathlib import Path
import aiohttp
from sophon import SophonManifest, SophonUpdate

async def main():
    old_build_url = "https://.../old_manifest"
    new_build_url = "https://.../new_manifest"
    
    game_dir = "./game"
    update_dir = "./game_updated"
    chunks_staging_dir = "./chunks_temp"

    async with aiohttp.ClientSession() as session:
        # Fetch both manifests
        old_pair = await SophonManifest.create_chunk_manifest_info_pair(session, old_build_url)
        new_pair = await SophonManifest.create_chunk_manifest_info_pair(session, new_build_url)

        # Enumerate only changed assets
        async for asset in SophonUpdate.enumerate_update_async(session, old_pair, new_pair):
            print(f"Updating {asset.asset_name}...")
            
            if asset.is_has_patch:
                # 1. Download missing difference chunks to staging area
                await asset.download_diff_chunks_async(session, chunks_staging_dir)
                
                # 2. Reconstruct new file using old file + diff chunks
                await asset.write_update_async(
                    session,
                    old_input_dir=game_dir,
                    new_output_dir=update_dir,
                    chunk_dir=chunks_staging_dir
                )
            else:
                # It's a completely new file
                out_path = Path(update_dir) / asset.asset_name
                out_path.parent.mkdir(parents=True, exist_ok=True)
                await asset.write_to_stream_async(session, str(out_path))

if __name__ == "__main__":
    asyncio.run(main())
```

## 3. Applying HDiffPatch Patches

Some games utilize `.hdiff` patches instead of chunk-based updates. Sophon supports applying these through `SophonPatch`.

*(Note: Requires the `hpatchz` binary accessible in your system path or specified via `HPATCHZ_PATH` environment variable)*

```python
import asyncio
import aiohttp
from sophon import SophonPatch, SophonManifest

async def main():
    patch_url = "https://.../patch_manifest"
    main_url = "https://.../main_manifest"
    version_from = "1.0.0"
    
    game_dir = "./game"
    patch_staging_dir = "./patches"

    async with aiohttp.ClientSession() as session:
        # Fetch the patch metadata for updating FROM a specific version
        patch_pair = await SophonPatch.create_chunk_manifest_info_pair(
            session, patch_url, version_tag_update_from=version_from
        )
        main_pair = await SophonManifest.create_chunk_manifest_info_pair(session, main_url)

        async for patch_asset in SophonPatch.enumerate_update_async(
            session, patch_pair, main_pair, version_from
        ):
            print(f"Processing patch for {patch_asset.target_file_path}")
            
            # Download the patch diff file
            await patch_asset.download_patch_async(
                session,
                input_dir=game_dir,
                patch_output_dir=patch_staging_dir
            )
            
            # Apply the patch using hpatchz or copy operations
            await patch_asset.apply_patch_update_async(
                session,
                input_dir=game_dir,
                patch_output_dir=patch_staging_dir,
                remove_old_assets=True
            )

if __name__ == "__main__":
    asyncio.run(main())
```
