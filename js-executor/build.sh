#!/bin/bash

# Build script for js-executor (Linux-focused deployment)
# Usage: ./build.sh

set -e

echo "🚀 Building ECharts js-executor for Linux deployment..."
echo ""

# Create output directory
mkdir -p ../bin

# Clean previous builds
echo "  → Cleaning previous builds..."
rm -f ../bin/echarts-convert-*

# Get Bun version
BUN_VERSION=$(bun --version)
echo "📦 Using Bun version: $BUN_VERSION"
echo ""

# =========================================================================
# PRODUCTION BUILDS - LINUX ONLY
# =========================================================================
# Only Linux binaries are included in the plugin package to minimize size
# Other platform builds are commented out for future reference

echo "🔨 Building production binaries for Linux..."

# Build for Linux x64 (main production target)
echo "  → Building for Linux x64..."
bun run build:prod:x64
if [ $? -eq 0 ]; then
    echo "    ✅ Linux x64 build successful"
else
    echo "    ❌ Linux x64 build failed"
    exit 1
fi

# Build for Linux ARM64 (secondary production target)
echo "  → Building for Linux ARM64..."
bun run build:prod:arm64
if [ $? -eq 0 ]; then
    echo "    ✅ Linux ARM64 build successful"
else
    echo "    ⚠️  Linux ARM64 build failed (optional for most deployments)"
fi

# Make Linux binaries executable
chmod +x ../bin/echarts-convert-linux-* 2>/dev/null

echo ""
echo "✅ Production Linux builds completed!"
echo ""

# =========================================================================
# DEVELOPMENT BUILDS - ALL PLATFORMS (COMMENTED OUT)
# =========================================================================
# Uncomment the following section if you need binaries for development
# or testing on other platforms. These are NOT included in production.

: <<'COMMENT_BLOCK'

echo "🔧 Building development binaries for all platforms..."

# Build for local debugging (current platform)
echo "  → Building for local debugging..."
bun run build:dev
if [ $? -eq 0 ]; then
    echo "    ✅ Local debug build successful"
else
    echo "    ⚠️  Local debug build failed"
fi

# Build for Windows x64
echo "  → Building for Windows x64..."
bun run build:dev-win
if [ $? -eq 0 ]; then
    echo "    ✅ Windows build successful"
else
    echo "    ⚠️  Windows build failed"
fi

# Make all binaries executable
chmod +x ../bin/echarts-convert-* 2>/dev/null || true

echo "✅ Development builds completed!"

COMMENT_BLOCK

# =========================================================================
# BUILD SUMMARY
# =========================================================================

echo "📊 Build Summary:"
echo ""
echo "Production binaries (included in plugin package):"
if [ -f "../bin/echarts-convert-linux-x64" ]; then
    echo "  ✅ echarts-convert-linux-x64 ($(du -h ../bin/echarts-convert-linux-x64 | cut -f1))"
else
    echo "  ❌ echarts-convert-linux-x64 (build failed)"
fi

if [ -f "../bin/echarts-convert-linux-arm64" ]; then
    echo "  ✅ echarts-convert-linux-arm64 ($(du -h ../bin/echarts-convert-linux-arm64 | cut -f1))"
else
    echo "  ⚠️  echarts-convert-linux-arm64 (optional, not built)"
fi

echo ""
echo "Total plugin binary size:"
if [ -d "../bin" ]; then
    total_size=$(du -sh ../bin | cut -f1)
    echo "  📦 $total_size"
fi

echo ""
echo "📝 Notes:"
echo "  • Only Linux binaries are packaged to minimize plugin size"
echo "  • For local debugging, build echarts-convert-local manually"
echo "  • Linux ARM64 build is optional but included for ARM server support"
echo "  • Use ECHARTS_CONVERT_LOCAL_PATH to specify custom executable path"