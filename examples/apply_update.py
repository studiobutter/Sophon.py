"""Example: Apply game updates using Sophon."""

import asyncio
from pathlib import Path

import aiohttp

from sophon.helper.progress import ProgressTracker, create_progress_callback


async def main():
    """
    Example showing how to apply updates with progress tracking.

    This example demonstrates:
    1. Fetching old and new manifests
    2. Enumerating changed assets
    3. Downloading and applying updates
    4. Tracking update progress with speed and ETA
    """

    game_dir = Path("./game")
    updates_dir = Path("./updates")
    game_dir.mkdir(exist_ok=True)
    updates_dir.mkdir(exist_ok=True)

    async with aiohttp.ClientSession():
        try:
            print("Fetching manifests...")
            # TODO: Create info pairs from URLs
            # old_manifest_pair = await SophonManifest.create_chunk_manifest_info_pair(...)
            # new_manifest_pair = await SophonManifest.create_chunk_manifest_info_pair(...)

            # Calculate total update size
            # total_size = sum(asset.asset_size for asset in ...)
            # progress = ProgressTracker(total_bytes=total_size)
            
            # print("Computing update differences...")
            # async for asset in SophonUpdate.enumerate_update_async(
            #     session, old_manifest_pair, new_manifest_pair
            # ):
            #     progress_callback = create_progress_callback(
            #         progress, 
            #         current_file=asset.asset_name
            #     )
            #     
            #     print(f"\nUpdating {asset.asset_name}...")
            #     
            #     # Download and apply update with progress tracking
            #     # await asset.write_update_async(
            #     #     session,
            #     #     str(game_dir),
            #     #     str(game_dir),
            #     #     str(updates_dir),
            #     #     download_info_delegate=progress_callback
            #     # )
            #     
            #     progress.reset_file()

            print("\n✓ Update complete!")
            # print(f"  Total time: {ProgressTracker.format_time(progress.elapsed_seconds)}")
            # print(f"  Average speed: {ProgressTracker.format_bytes(progress.average_speed)}/s")

        except Exception as e:
            print(f"Error: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
