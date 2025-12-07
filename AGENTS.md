# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Important Rules

### Dify Documentation
For ANY question about Dify (plugin development, API usage, configuration, troubleshooting, etc.), use the llms-docs MCP server to help answer. The llms-docs MCP server provides comprehensive documentation and examples for all Dify-related topics.

## Plugin Overview

This is a Dify plugin for converting ECharts visualizations to images. It's structured as a tool provider plugin that extends Dify's capabilities to generate chart images from ECharts configurations.

## Architecture

### Plugin Structure
- **Main Entry Point**: `main.py` - Simple plugin bootstrap using dify_plugin SDK
- **Provider Layer**: `provider/echarts-convert.py` - Tool provider with credential validation
- **Tool Implementation**: `tools/echarts-convert.py` - Actual chart conversion logic (currently stub implementation)
- **Configuration**: YAML files defining plugin metadata and tool parameters

### Key Components
1. **manifest.yaml** - Plugin metadata, permissions, and resource requirements
2. **Provider** (`provider/echarts-convert.py`) - Manages tool validation and authentication
3. **Tool** (`tools/echarts-convert.py`) - Implements the chart conversion functionality

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
# Package plugin manually
dify-plugin plugin package ./

# Automated publishing via GitHub Actions (creates release PR)
# Triggered automatically when creating a GitHub release
```

## Plugin Configuration

### Resource Allocation
- Memory: 256MB (268435456 bytes)
- Storage: 1MB for file operations
- Architecture: amd64, arm64
- Python Runtime: 3.12

### Permissions
- Tool operations: Enabled
- Storage access: Enabled (1MB limit)

## Implementation Status

**Current State**: Fully functional with advanced concurrency support
- ✅ ECharts to SVG conversion implemented using JavaScript Node.js/Bun runtime
- ✅ Real-time logging system for JavaScript execution process
- ✅ Concurrent rendering with configurable worker threads (1-4)
- ✅ Comprehensive performance testing and optimization
- ✅ Error handling and validation for chart configurations
- ✅ Support for batch processing multiple charts

**Key Performance Insights**:
- Concurrent rendering provides significant benefits (40-50% improvement) for heavy-duty charts
- Sequential rendering remains optimal for simple charts
- Worker overhead is minimal when processing complex charts with 1000+ data points

**Architecture Components**:
1. **JavaScript Runtime** (`js-executor/`) - ECharts rendering engine with Worker thread support
   - `index.ts` - Main process coordination with detailed timing logs
   - `render.ts` - Core chart rendering function with comprehensive logging
   - `worker.ts` - Worker thread implementation for parallel processing
   - `performance-test.js` - Performance testing utilities

2. **Python Integration** (`tools/utils/renderer.py`) - Real-time log capture and process management
   - Threading-based log streaming from JavaScript subprocess
   - Comprehensive timing breakdown and error handling

**Concurrency Performance Characteristics**:
- **Heavy Charts** (1000+ data points): 40-50% performance improvement with 2-4 workers
- **Simple Charts** (<100 data points): Sequential rendering recommended
- **Optimal Use Cases**: Small batches (2-3 charts) of complex visualizations

**Next Steps for Development**:
1. Add support for additional image formats (PNG, JPEG) beyond SVG
2. Implement adaptive concurrency that automatically chooses optimal worker count based on chart complexity
3. Add chart complexity detection to provide user recommendations
4. Implement caching for repeated chart configurations
5. Consider adding GPU acceleration for extremely large datasets

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
│       └── renderer.py        # ECharts renderer with concurrent processing
├── js-executor/               # JavaScript ECharts rendering engine
│   ├── index.ts              # Main process coordination and CLI interface
│   ├── render.ts             # Core ECharts rendering function
│   ├── worker.ts             # Worker thread implementation
│   ├── performance-test.js   # Heavy-duty chart performance testing
│   ├── package.json          # Node.js/Bun dependencies
│   ├── tsconfig.json         # TypeScript configuration
│   └── test.json             # Sample chart configurations for testing
├── _assets/                   # Plugin icons
└── readme/                    # Multi-language README files
```