# Sophon.py
Sophon protocol implementation in Python

> [!IMPORTANT]  
> This project should only be used for reference as the entire project is AI Generated. It s advised that Developers should handle their own implementation and recreate the project from blank.
> The reason I'm saying this because many developers may not like AI Generated codes on their work.

## Project Structure

```
sophon/                 # Main package
├── __init__.py        # Package initialization
├── asset.py           # SophonAsset for file downloads
├── manifest.py        # SophonManifest for manifest handling
├── update.py          # SophonUpdate for update logic
├── patch.py           # SophonPatch for patch operations
├── chunk.py           # SophonChunk and related structures
├── speed_limiter.py   # Download speed limiter
├── exceptions.py      # Custom exceptions
├── types/             # Type definitions
│   ├── __init__.py
│   ├── manifest_info.py
│   ├── chunks_info.py
│   └── info_pair.py
├── helper/            # Helper utilities
│   ├── __init__.py
│   └── extensions.py
└── proto/             # Protocol buffer definitions
    └── __init__.py

tests/                  # Test suite
examples/               # Example scripts
```

## Installation

```bash
pip install -e .
```

## Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Format code:

```bash
black sophon tests examples
```

Lint code:

```bash
ruff check sophon tests examples
```

## Usage Examples

### Basic Manifest Enumeration

```python
import asyncio
import aiohttp
from sophon import SophonManifest

async def main():
    async with aiohttp.ClientSession() as session:
        manifest_pair = await SophonManifest.create_chunk_manifest_info_pair(
            session, "https://api-os.hoyoverse.com/launcher_api/v1/manifest"
        )
        
        async for asset in SophonManifest.enumerate_async(session, manifest_pair):
            print(f"{asset.asset_name}: {asset.asset_size} bytes")

asyncio.run(main())
```

### Download Asset

```python
import asyncio
import aiohttp
from sophon import SophonManifest

async def main():
    async with aiohttp.ClientSession() as session:
        manifest_pair = await SophonManifest.create_chunk_manifest_info_pair(
            session, "https://..."
        )
        
        async for asset in SophonManifest.enumerate_async(session, manifest_pair):
            await asset.write_to_stream_async(
                session, 
                f"./downloads/{asset.asset_name}"
            )

asyncio.run(main())
```

### Apply Update

```python
import asyncio
import aiohttp
from sophon import SophonManifest, SophonUpdate

async def main():
    async with aiohttp.ClientSession() as session:
        old_manifest = await SophonManifest.create_chunk_manifest_info_pair(
            session, "https://old_version_url"
        )
        new_manifest = await SophonManifest.create_chunk_manifest_info_pair(
            session, "https://new_version_url"
        )
        
        async for asset in SophonUpdate.enumerate_update_async(
            session, old_manifest, new_manifest
        ):
            await asset.write_update_async(
                session, 
                "./old_game",
                "./new_game",
                "./chunks"
            )

asyncio.run(main())
```

## Key Features

- **Async/Await Support**: Full async support using aiohttp and asyncio
- **Chunk-Based Downloads**: Efficient file downloading with chunk verification
- **Update Support**: Incremental game updates with diff patching
- **Speed Limiting**: Optional download speed control
- **Type Safety**: Full type hints for IDE support
- **Cross-Platform**: Works on Windows, macOS, and Linux

## License

MIT

## Related Projects

- [Hi3Helper.Sophon](https://github.com/CollapseLauncher/Hi3Helper.Sophon) - Original C# implementation
- [Collapse Launcher](https://github.com/CollapseLauncher/Collapse) - Game launcher using Sophon
