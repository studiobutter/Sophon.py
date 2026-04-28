# Getting Started with Sophon.py

Welcome to the Sophon.py workspace! This is a Python port of the Hi3Helper.Sophon library for downloading HoYoverse games.

## Workspace Structure

```
Sophon.py/
├── .github/
│   └── copilot-instructions.md
├── .vscode/
│   ├── settings.json
│   └── launch.json
├── sophon/                    # Main package
│   ├── __init__.py
│   ├── asset.py              # Download functionality
│   ├── manifest.py           # Manifest handling
│   ├── update.py             # Update logic
│   ├── patch.py              # Patching operations
│   ├── chunk.py              # Chunk structures
│   ├── speed_limiter.py      # Speed control
│   ├── exceptions.py         # Custom exceptions
│   ├── py.typed              # Type hints marker
│   ├── types/                # Type definitions
│   │   ├── __init__.py
│   │   ├── manifest_info.py
│   │   ├── chunks_info.py
│   │   └── info_pair.py
│   ├── helper/               # Utilities
│   │   ├── __init__.py
│   │   └── extensions.py
│   └── proto/                # Protocol buffers
│       └── __init__.py
├── tests/                    # Test suite
│   ├── __init__.py
│   └── test_manifest.py
├── examples/                 # Example scripts
│   ├── __init__.py
│   ├── basic_manifest_fetch.py
│   ├── download_assets.py
│   └── apply_update.py
├── .gitignore
├── pyproject.toml            # Package configuration
├── setup.py                  # Legacy setup
├── README.md                 # Project README
└── GETTING_STARTED.md        # This file
```

## Quick Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
```

### 2. Install Dependencies

```bash
# Install package in development mode
pip install -e .

# Install development tools
pip install -e ".[dev]"
```

### 3. Verify Installation

```bash
python -c "import sophon; print(sophon.__version__)"
```

## Development Workflow

### Running Tests

```bash
pytest                    # Run all tests
pytest tests/test_manifest.py  # Run specific test file
pytest -v --cov          # Run with coverage
```

### Code Formatting

```bash
black sophon tests examples  # Format code
isort sophon tests examples  # Organize imports
ruff check sophon           # Lint code
mypy sophon                # Type checking
```

### Running Examples

```bash
python examples/basic_manifest_fetch.py
python examples/download_assets.py
python examples/apply_update.py
```

## Key Components

### SophonAsset (`sophon/asset.py`)
Handles file downloads with chunk support:
- Download full files
- Download diff chunks (for updates)
- Parallel chunk downloads
- Hash verification
- Progress tracking

### SophonManifest (`sophon/manifest.py`)
Manages manifest fetching and enumeration:
- Fetch manifests from HoYoverse API
- Parse manifest data
- Enumerate assets
- Create info pairs

### SophonUpdate (`sophon/update.py`)
Handles game updates:
- Compare old and new manifests
- Identify changed assets
- Enumerate update-only assets
- Efficient incremental updates

### SophonPatch (`sophon/patch.py`)
Applies binary patches using HDiffPatch:
- Download patches
- Apply HDiff patches
- Handle multiple patch methods
- Support for various patch formats

## Architecture Overview

The Python port maintains the same core architecture as the C# version:

1. **Async/Await Pattern**: Uses `aiohttp` for HTTP requests and `asyncio` for async operations
2. **Type Safety**: Full type hints for IDE support
3. **Protocol Buffers**: Uses protobuf for efficient data serialization
4. **Modular Design**: Separated concerns across focused modules
5. **Error Handling**: Custom exceptions for different error scenarios

## Implementation Status

- ✅ **Completed (100%)**: Sequential & Parallel download engine, Chunk verification, Data structures/types, Exception framework, Speed limiter, Manifest handling (enumeration works), Protocol Buffer compilation, Update/Patch Logic (HDiffPatch integration), Zstandard compression, Test framework (Unit tests done, integration tests needed), Documentation.
- ⚠️ **Partially Complete (20-40%)**: *empty*
- ❌ **Not Started (0-5%)**: *empty*

**🔴 Critical Blockers:**
None. Core logic is completely mapped and ported. Next phase is robust verification.

## Next Steps

1. **Write Integration Tests** (2-3 hours)
2. **Setup CI/CD pipeline** (1-2 hours)

## Resources

- [aiohttp Documentation](https://docs.aiohttp.org/)
- [Protocol Buffers Python](https://developers.google.com/protocol-buffers/docs/pythontutorial)
- [asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
- [Original Hi3Helper.Sophon](https://github.com/CollapseLauncher/Hi3Helper.Sophon)

## Support

For issues and questions:
1. Check the [README.md](./README.md)
2. Review the examples in `examples/`
3. Check existing tests in `tests/`
4. Refer to the original C# implementation for logic

---

Happy coding! 🚀
