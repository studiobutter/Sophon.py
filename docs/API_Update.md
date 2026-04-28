# SophonUpdate API

`SophonUpdate` provides utilities for handling game updates incrementally by comparing old and new manifests.

## Methods

### `enumerate_update_async`
```python
@staticmethod
async def enumerate_update_async(
    http_client: aiohttp.ClientSession,
    info_pair_old: SophonChunkManifestInfoPair,
    info_pair_new: SophonChunkManifestInfoPair,
    remove_chunk_after_apply: bool = False,
    download_speed_limiter: Optional[SophonDownloadSpeedLimiter] = None,
    token: Optional[asyncio.CancelledError] = None,
) -> AsyncIterator[SophonAsset]
```
Enumerates changed assets between an old manifest and a new manifest. This allows efficient incremental updates by only yielding assets that have changed or are completely new. For assets that have changed, it correctly links old chunk offsets if their hashes match to allow differential updates.

**Arguments:**
- `http_client`: The `aiohttp.ClientSession` to use.
- `info_pair_old`: Old manifest and chunks info pair.
- `info_pair_new`: New manifest and chunks info pair.
- `remove_chunk_after_apply`: Removes chunks after applying the update.
- `download_speed_limiter`: Optional speed limiter.
- `token`: Cancellation token.

**Yields:**
- `SophonAsset`: Represents assets that have changed or are new.
