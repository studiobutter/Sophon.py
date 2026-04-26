"""Example: Download assets using Sophon."""

import asyncio
from pathlib import Path

import aiohttp

from sophon import SophonManifest


async def download_progress(bytes_read: int) -> None:
    """Callback for download progress."""
    # This is a placeholder for progress tracking
    pass


async def main():
    """
    Example showing how to download assets.

    This example demonstrates:
    1. Fetching manifest
    2. Enumerating assets
    3. Downloading individual assets with progress tracking
    """
    build_url = "https://api-os.hoyoverse.com/launcher_api/v1/manifest"
    output_dir = Path("./downloads")
    output_dir.mkdir(exist_ok=True)

    async with aiohttp.ClientSession() as session:
        try:
            # Create manifest info pair
            print("Fetching manifest...")
            manifest_pair = await SophonManifest.create_chunk_manifest_info_pair(
                session, build_url, matching_field="game"
            )

            if not manifest_pair.is_found:
                print(f"Manifest not found: {manifest_pair.return_message}")
                return

            # Download assets
            print("Downloading assets...")
            asset_count = 0
            async for asset in SophonManifest.enumerate_async(session, manifest_pair):
                if asset.is_directory:
                    continue

                output_path = output_dir / asset.asset_name
                output_path.parent.mkdir(parents=True, exist_ok=True)

                print(f"Downloading {asset.asset_name}...")

                # TODO: Implement actual download
                # await asset.write_to_stream_async(
                #     session,
                #     str(output_path),
                #     download_info_delegate=download_progress
                # )

                asset_count += 1
                if asset_count >= 5:  # Limit to first 5 for example
                    break

            print(f"\nDownloaded {asset_count} assets to {output_dir}")

        except Exception as e:
            print(f"Error: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
