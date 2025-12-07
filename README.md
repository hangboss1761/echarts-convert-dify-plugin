# ECharts to Image Converter

**Author:** hangboss1761
**Version:** 0.0.1
**Type:** tool
**Repository:** <https://github.com/hangboss1761/echarts-convert-dify-plugin>

## Overview

ECharts to Image Converter is a powerful Dify plugin that converts ECharts configurations in text to high-quality images. The plugin supports batch processing, concurrent rendering, and flexible output format configuration.

**Use Case**: Perfect for converting ECharts chart configurations from markdown strings into images, then converting complete markdown strings to docx/pdf formats (use `md_exporter` plugin).

![usecase](./_assets/image.png)

This plugin runs completely offline with zero external dependencies.

> Echarts version: 5.6.0

## Configuration

The ECharts to Image Converter provides the following configuration options:

### Input Parameters

- **Content**: Text containing ````echarts```` code blocks with ECharts JSON configurations (required)
- **Image Type**: Output image format (`svg` - SVG only)
- **Width**: Chart width in pixels (100-4000, default: 800)
- **Height**: Chart height in pixels (100-4000, default: 600)

### Advanced Options

- **Worker Count**: Number of worker processes for concurrent rendering (1-4, default: 1)
  - **Recommendation**: Use 2-4 for complex charts, 1 for simple charts
- **Merge ECharts Options**: Additional ECharts options in JSON format (optional)

### ⚡ Concurrency Performance Guide

**Use Concurrency** (2-4 workers):
- Complex charts with large datasets
- Multi-series visualizations
- Performance depends on your hardware capabilities

**Use Sequential** (not use workers):
- Simple charts (bar, pie, line)
- Small datasets
- Single chart rendering

**Note**: Performance gains vary based on device specifications and chart complexity.

## Development

### Development Setup

copy `.env.example` to `.env` and fill in the values.

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install js-executor dependencies (for development only)
cd js-executor
# Install Bun: <https://bun.sh/docs/installation>
# skip if you have already installed Bun
bun install

# Run in development mode
python -m main

# Run in development mode with local binary, use pnpm build:dev to build the local binary.
ECHARTS_CONVERT_LOCAL_PATH=./bin/echarts-convert-local python -m main

# More info in GUIDE.md
```

**Note:** For production deployment in Dify, the plugin requires **zero external dependencies**. All JavaScript runtime dependencies are bundled with the plugin, enabling complete offline operation without requiring any external API calls or internet connectivity.

then add the plugin in Dify workflow and test it.

## Usage Example

```markdown
# Example Chart

```echarts
{
  "title": {
    "text": "Sample Chart"
  },
  "xAxis": {
    "type": "category",
    "data": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
  },
  "yAxis": {
    "type": "value"
  },
  "series": [{
    "data": [120, 200, 150, 80, 70, 110, 130],
    "type": "bar"
  }]
}
```

some text ...

```
---

The plugin will automatically extract the ECharts configuration and convert it to the specified image format.


