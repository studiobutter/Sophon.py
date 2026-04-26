"""Example: Apply game updates using Sophon."""

import asyncio
from pathlib import Path

import aiohttp


async def main():
    """
    Example showing how to apply updates.

    This example demonstrates:
    1. Fetching old and new manifests
    2. Enumerating changed assets
    3. Downloading and applying updates
    """

    Path("./game")
    Path("./updates")

    async with aiohttp.ClientSession():
        try:
            print("Fetching manifests...")
            # TODO: Create info pairs from URLs
            # old_manifest_pair = await SophonManifest.create_chunk_manifest_info_pair(...)
            # new_manifest_pair = await SophonManifest.create_chunk_manifest_info_pair(...)

            # print("Computing update differences...")
            # async for asset in SophonUpdate.enumerate_update_async(
            #     session, old_manifest_pair, new_manifest_pair
            # ):
            #     print(f"Updating {asset.asset_name}...")
            #     # Download and apply update

            print("Update complete!")

        except Exception as e:
            print(f"Error: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
