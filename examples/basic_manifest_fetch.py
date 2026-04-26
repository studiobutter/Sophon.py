"""Basic example: Fetch manifest and enumerate assets."""

import asyncio

import aiohttp

from sophon import SophonManifest


async def main():
    """
    Basic example showing how to fetch a manifest and enumerate assets.

    This example demonstrates:
    1. Creating a ClientSession for HTTP requests
    2. Creating manifest info pair from a branch URL
    3. Enumerating assets from the manifest
    """
    # Example URLs (replace with actual Sophon API endpoints)
    build_url = "https://api-os.hoyoverse.com/launcher_api/v1/manifest"

    async with aiohttp.ClientSession() as session:
        try:
            # Create manifest info pair from branch URL
            print("Fetching manifest information...")
            manifest_pair = await SophonManifest.create_chunk_manifest_info_pair(
                session, build_url, matching_field="game"
            )

            if not manifest_pair.is_found:
                print(f"Manifest not found: {manifest_pair.return_message}")
                return

            print(f"Manifest found: {manifest_pair}")
            print(f"Total files: {manifest_pair.chunks_info.files_count}")
            print(f"Total size: {manifest_pair.chunks_info.total_size / (1024**3):.2f} GB")

            # Enumerate assets from manifest
            print("\nEnumerating assets:")
            asset_count = 0
            async for asset in SophonManifest.enumerate_async(session, manifest_pair):
                if not asset.is_directory:
                    asset_count += 1
                    print(f"  {asset.asset_name} ({asset.asset_size} bytes)")

            print(f"\nTotal assets: {asset_count}")

        except Exception as e:
            print(f"Error: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
