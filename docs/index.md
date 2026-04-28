# Sophon.py Documentation

Welcome to the documentation for **Sophon.py**, a robust Python port of the Hi3Helper.Sophon library. Sophon.py is designed to handle downloading and updating HoYoverse games, featuring async support, chunk-based downloads, and incremental patch application.

## Core Features

- **Async/Await Support**: Fully leverages `aiohttp` and `asyncio` for high-performance network requests and asynchronous operations.
- **Chunk-Based Downloads**: Supports full and incremental downloads, utilizing chunk verification to ensure data integrity.
- **Protocol Buffers**: Employs Protobuf v3 for efficient data serialization and deserialization.
- **Update Logic**: Capable of comparing old and new manifests to identify changed or update-only assets, streamlining the update process.
- **Binary Patching**: Integrates `HDiffPatch` to apply binary diffs for incremental updates.
- **Speed Limiting**: Built-in speed control mechanism for throttling network usage.
- **Type Safety**: Thoroughly type-hinted for excellent IDE support and code maintainability.

## Main Components

The `sophon` package consists of several crucial modules:

- **`SophonAsset` (`sophon/asset.py`)**: Responsible for file downloads. It handles both full files and diff chunks, supporting parallel downloads, hash verification, and progress tracking.
- **`SophonManifest` (`sophon/manifest.py`)**: Manages fetching and parsing of manifests from the HoYoverse API, enabling asset enumeration.
- **`SophonUpdate` (`sophon/update.py`)**: Focuses on update logic by comparing manifests to detect changes and generate efficient incremental updates.
- **`SophonPatch` (`sophon/patch.py`)**: Handles binary patch downloading and application using HDiffPatch.

## Getting Started

To get started with development or to use this library, refer to the [Getting Started guide](./GETTING_STARTED.md) and the [Project README](../README.md).

You can also explore the example scripts provided in the `examples/` directory for practical implementations such as basic manifest fetching, downloading assets, and applying updates.
