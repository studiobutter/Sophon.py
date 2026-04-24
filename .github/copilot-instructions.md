<!-- Sophon.py Project Instructions -->

- [x] Verify that the copilot-instructions.md file in the .github directory is created.
- [x] Clarify Project Requirements
- [x] Scaffold the Project
- [x] Customize the Project
- [ ] Install Required Extensions
- [ ] Compile the Project
- [ ] Create and Run Task
- [ ] Launch the Project
- [ ] Ensure Documentation is Complete

## Project Overview

**Sophon.py** is a Python port of the Hi3Helper.Sophon library for downloading HoYoverse games using the Sophon protocol.

### Key Technologies
- Python 3.9+
- aiohttp for async HTTP requests
- Protocol Buffers for data serialization
- Zstandard for compression
- Pydantic for data validation

### Project Status
- Project structure: Complete
- Core modules: Stubs created
- Type definitions: Complete
- Helper utilities: Partial
- Tests: Basic framework
- Examples: Created
- Documentation: Created

### Next Steps
1. Install Python dependencies (pip install -e .[dev])
2. Configure VS Code Python environment
3. Implement core async download logic
4. Add Protocol Buffers integration
5. Implement update/patch logic
6. Add comprehensive tests
7. Create CI/CD pipeline

### Development Commands
```bash
# Install package
pip install -e .

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black sophon tests examples

# Lint
ruff check sophon tests examples

# Type checking
mypy sophon
```

### Module Structure
- **sophon/asset.py**: File download functionality
- **sophon/manifest.py**: Manifest management
- **sophon/update.py**: Update logic
- **sophon/patch.py**: Patching operations
- **sophon/types/**: Data structures
- **sophon/helper/**: Utilities
- **sophon/proto/**: Protocol Buffer stubs
