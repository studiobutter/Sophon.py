# SophonAsset API

`SophonAsset` represents a single asset (file) to be downloaded via the Sophon protocol. It provides methods to download chunks, perform differential downloads, and apply updates.

## Properties
- `asset_name` (`str`): Name of the asset.
- `asset_size` (`int`): Size of the asset in bytes.
- `asset_hash` (`Optional[str]`): Hash of the asset.
- `is_directory` (`bool`): True if the asset represents a directory.
- `is_has_patch` (`bool`): True if the asset has an associated patch/diff.
- `chunks` (`list[SophonChunk]`): List of chunks making up the asset.

## Methods

### `write_to_stream_async`
```python
async def write_to_stream_async(
    self,
    client: aiohttp.ClientSession,
    output_path: str,
    parallel_options: Optional[ParallelOptions] = None,
    write_info_delegate: Optional[Callable[[int], None]] = None,
    download_info_delegate: Optional[Callable[[int, int], None]] = None,
    download_complete_delegate: Optional[Callable[["SophonAsset"], None]] = None,
    token: Optional[asyncio.CancelledError] = None,
) -> None
```
Downloads the asset file by fetching its chunks and writing them to `output_path`. Optionally supports parallel downloads and progress tracking via delegates.

---

### `download_diff_chunks_async`
```python
async def download_diff_chunks_async(
    self,
    client: aiohttp.ClientSession,
    chunk_dir_output: str,
    parallel_options: Optional[ParallelOptions] = None,
    ...
) -> None
```
Downloads and stages diff chunks for update or preload operations into `chunk_dir_output`. Only chunks that aren't available locally or from an old file are downloaded.

---

### `write_update_async`
```python
async def write_update_async(
    self,
    client: aiohttp.ClientSession,
    old_input_dir: str,
    new_output_dir: str,
    chunk_dir: str,
    remove_chunk_after_apply: bool = False,
    ...
) -> None
```
Applies an update to an existing file or creates a new file. It combines locally available chunks from `old_input_dir`, staged diff chunks from `chunk_dir`, and potentially downloads missing chunks from the internet, then writes the updated file to `new_output_dir`.
