# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Important Rules

### Dify Documentation
For ANY question about Dify (plugin development, API usage, configuration, troubleshooting, etc.), use the llms-docs MCP server to help answer. The llms-docs MCP server provides comprehensive documentation and examples for all Dify-related topics.

## Plugin Overview

This is a Dify plugin for converting ECharts visualizations to images. It's structured as a tool provider plugin that extends Dify's capabilities to generate chart images from ECharts configurations.

## Documentation

**Important**: For detailed system requirements and design documentation, please refer to:
- **Product Requirements**: `docs/prd.md` - Complete product requirements and functional specifications
- **Design Documentation**: `docs/design.md` - System architecture, module design, and design decisions

**Documentation Maintenance**: When making code changes, ensure that `docs/prd.md` and `docs/design.md` are updated to reflect the current implementation. These documents should always match the actual code behavior.

## Architecture

### Plugin Structure
- **Main Entry Point**: `main.py` - Simple plugin bootstrap using dify_plugin SDK
- **Provider Layer**: `provider/echarts-convert.py` - Tool provider with credential validation
- **Tool Implementation**: `tools/echarts-convert.py` - Chart conversion logic with full rendering support
- **Configuration**: YAML files defining plugin metadata and tool parameters

### Key Components
1. **manifest.yaml** - Plugin metadata, permissions, and resource requirements
2. **Provider** (`provider/echarts-convert.py`) - Manages tool validation and authentication
3. **Tool** (`tools/echarts-convert.py`) - Implements the chart conversion functionality
4. **Utilities** (`tools/utils/`) - Supporting modules for parsing, rendering, binary management, and version management
5. **JavaScript Executor** (`js-executor/`) - ECharts rendering engine with concurrent processing support

## Development Commands

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment for debugging
cp .env.example .env
# Edit .env with your debug configuration

# Run plugin in debug mode
python -m main
```

### Testing
The plugin can be tested by connecting to a Dify instance with remote debugging enabled. Configure the `.env` file with:
- `INSTALL_METHOD=remote`
- `REMOTE_INSTALL_URL=debug.dify.ai:5003`
- `REMOTE_INSTALL_KEY=your-debug-key`

### Packaging and Publishing
```bash
# Build and package plugin using build script (version automatically read from manifest.yaml)
./build.sh

# Include arm64 binary as well
INCLUDE_ARM64=true ./build.sh

# Build with specific version (overrides manifest.yaml)
VERSION=1.0.0 ./build.sh

# Clean build artifacts
./build.sh clean

# For CI/GitHub Actions
./build.sh ci

# Automated publishing via GitHub Actions (creates release PR)
# Triggered automatically when creating a GitHub release
```

**Version Management**:
- Build scripts automatically read version from `manifest.yaml`
- Versioned binary files are created: `echarts-convert-{version}-linux-{arch}`
- Old versions are automatically cleaned to save storage space
- If current version not found, uses latest available version

## Plugin Configuration

### Resource Allocation
- Memory: 256MB (268435456 bytes)
- Architecture: amd64, arm64 (Architecture support)
- **Packaging**: Only Linux amd64 binary is included in the plugin package (.difypkg) due to the 50MB size limit
- Python Runtime: 3.12

**Note on Architecture Support**:
- The plugin architecture supports both Linux amd64 and Linux arm64
- However, only Linux amd64 binary is included in the production package to keep the .difypkg file under 50MB
- For development/testing, you can build with `INCLUDE_ARM64=true` to include arm64 binary

### Permissions
- Tool operations: Enabled
- Storage access: Enabled (1MB limit)

## File Structure

```
├── main.py                     # Plugin entry point
├── manifest.yaml              # Plugin metadata and configuration
├── requirements.txt           # Python dependencies
├── provider/
│   ├── echarts-convert.py     # Tool provider implementation
│   └── echarts-convert.yaml   # Provider configuration
├── tools/
│   ├── echarts-convert.py     # Tool implementation with full rendering logic
│   ├── echarts-convert.yaml   # Tool parameter definition
│   └── utils/
│       ├── parser.py          # Text parsing and code block extraction
│       ├── renderer.py        # Chart renderer with executor management
│       ├── binary_manager.py # Binary file decompression and caching
│       ├── version_manager.py # Version management and binary selection
│       └── logger.py          # Logging utilities
├── js-executor/               # JavaScript ECharts rendering engine
│   ├── index.ts              # Main process coordination and CLI interface
│   ├── render.ts             # Core ECharts rendering function
│   ├── worker.ts             # Worker thread implementation
│   ├── package.json          # Node.js/Bun dependencies
│   ├── tsconfig.json         # TypeScript configuration
│   └── test.json             # Sample chart configurations for testing
├── _assets/                   # Plugin icons
└── readme/                    # Multi-language README files
```