# SophonManifest API

`SophonManifest` is responsible for managing and downloading manifests in the Sophon protocol. It interacts with the branch API to fetch manifest information and can enumerate assets defined in a manifest.

## Methods

### `create_chunk_manifest_info_pair`
```python
@staticmethod
async def create_chunk_manifest_info_pair(
    client: aiohttp.ClientSession,
    url: str,
    matching_field: str = "game",
    is_throw_if_not_found: bool = True,
    token: Optional[asyncio.CancelledError] = None,
) -> SophonChunkManifestInfoPair
```
Creates a manifest info pair from a branch API endpoint.

**Arguments:**
- `client`: The `aiohttp.ClientSession` used for requests.
- `url`: Branch API URL.
- `matching_field`: Matching field name (usually `"game"`).
- `is_throw_if_not_found`: If `True`, raises a `ValueError` if the manifest is not found.
- `token`: Optional cancellation token.

**Returns:**
- `SophonChunkManifestInfoPair`: An object containing both manifest and chunk metadata.

---

### `enumerate_async`
```python
@staticmethod
async def enumerate_async(
    http_client: aiohttp.ClientSession,
    info_pair: SophonChunkManifestInfoPair,
    download_speed_limiter: Optional[SophonDownloadSpeedLimiter] = None,
    token: Optional[asyncio.CancelledError] = None,
) -> AsyncIterator[SophonAsset]
```
Enumerates assets from a manifest info pair.

**Arguments:**
- `http_client`: The `aiohttp.ClientSession` used for requests.
- `info_pair`: The manifest and chunks info pair returned by `create_chunk_manifest_info_pair`.
- `download_speed_limiter`: Optional speed limiter.
- `token`: Optional cancellation token.

**Yields:**
- `SophonAsset`: The assets contained in the manifest.
