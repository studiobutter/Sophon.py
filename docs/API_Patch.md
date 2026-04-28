# SophonPatch API

`SophonPatch` and `SophonPatchAsset` handle game patches and updates using the HDiffPatch mechanism. They manage patch enumeration, download, and application.

## `SophonPatch`

### `create_chunk_manifest_info_pair`
```python
@staticmethod
async def create_chunk_manifest_info_pair(
    client: aiohttp.ClientSession,
    url: str,
    version_tag_update_from: str,
    matching_field: Optional[str] = None,
    token: Optional[asyncio.CancelledError] = None,
) -> SophonChunkManifestInfoPair
```
Creates a patch manifest info pair from a patch API URL, targeting an update from a specific version tag.

### `enumerate_update_async`
```python
@staticmethod
async def enumerate_update_async(
    http_client: aiohttp.ClientSession,
    patch_info_pair: Optional[SophonChunkManifestInfoPair],
    main_info_pair: SophonChunkManifestInfoPair,
    version_tag_update_from: str,
    download_speed_limiter: Optional[SophonDownloadSpeedLimiter] = None,
    token: Optional[asyncio.CancelledError] = None,
) -> AsyncIterator[SophonPatchAsset]
```
Enumerates patch assets for updating from a specific version. Yields `SophonPatchAsset` objects containing patch methodology and metadata.

---

## `SophonPatchAsset`

### Properties
- `patch_method` (`SophonPatchMethod`): Indicates how the patch should be applied (e.g., `PATCH`, `COPY_OVER`, `DOWNLOAD_OVER`, `REMOVE`).
- `original_file_path`, `target_file_path`: Relative paths of the old and new files.
- `patch_size`, `patch_offset`: Patch metadata properties.

### Methods

#### `download_patch_async`
```python
async def download_patch_async(
    self,
    client: aiohttp.ClientSession,
    input_dir: str,
    patch_output_dir: str,
    force_verification: bool = False,
    ...
) -> bool
```
Downloads the patch file to `patch_output_dir`. Automatically skips downloading if a valid patch is already present.

#### `apply_patch_update_async`
```python
async def apply_patch_update_async(
    self,
    client: aiohttp.ClientSession,
    input_dir: str,
    patch_output_dir: str,
    remove_old_assets: bool = True,
    ...
) -> None
```
Applies the patch according to its `patch_method`. If the method is `PATCH`, it executes the external `hpatchz` binary to perform a binary difference patch.
