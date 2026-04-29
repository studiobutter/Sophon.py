"""Example: Download assets using Sophon."""

import asyncio
from pathlib import Path

import aiohttp

from sophon import SophonManifest
from sophon.helper.progress import ProgressTracker, create_progress_callback


async def main():
    """
    Example showing how to download assets.

    This example demonstrates:
    1. Fetching manifest
    2. Enumerating assets
    3. Downloading individual assets with progress tracking
    4. Using advanced progress tracking with speed and ETA
    """
    build_url = "<BUILD_URL>"
    output_dir = Path(r"C:\Games\Sophon_Test")
    output_dir.mkdir(exist_ok=True)
    # NOTE: The matching_field may need to be adjusted based on the actual manifest structure, since it is use for both game resources and voice resources.
    MAIN_FIELD = "game"
    VOICE_FIELD = "voice"

    async with aiohttp.ClientSession() as session:
        try:
            # Create manifest info pair
            print("Fetching manifest...")
            manifest_pair = await SophonManifest.create_chunk_manifest_info_pair(
                session, build_url, matching_field=MAIN_FIELD
            )

            if not manifest_pair.is_found:
                print(f"Manifest not found: {manifest_pair.return_message}")
                return

            # Calculate total size for progress tracking
            print("Calculating total download size...")
            total_size = 0
            asset_list = []
            async for asset in SophonManifest.enumerate_async(session, manifest_pair):
                if not asset.is_directory:
                    total_size += asset.asset_size
                    asset_list.append(asset)

            # Create progress tracker
            progress = ProgressTracker(total_bytes=total_size)

            # Download assets
            print(f"Downloading {len(asset_list)} assets ({ProgressTracker.format_bytes(total_size)})...\n")
            asset_count = 0
            for asset in asset_list:
                output_path = output_dir / asset.asset_name
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Create progress callback for this asset
                progress_callback = create_progress_callback(progress, current_file=asset.asset_name)

                await asset.write_to_stream_async(
                    session,
                    str(output_path),
                    download_info_delegate=progress_callback
                )

                progress.reset_file()
                asset_count += 1
                print()  # Add a newline after the progress text

            print(f"\n✓ Downloaded {asset_count} assets to {output_dir}")
            print(f"  Total time: {ProgressTracker.format_time(progress.elapsed_seconds)}")
            print(f"  Average speed: {ProgressTracker.format_bytes(progress.average_speed)}/s")

        except Exception as e:
            print(f"Error: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
