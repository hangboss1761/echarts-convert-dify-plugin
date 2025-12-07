# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Project Overview

This is a JavaScript/TypeScript execution environment built with Bun. It appears to be a component for the echarts-convert plugin, providing a Node.js-like runtime for JavaScript execution, likely for processing ECharts configurations or running JavaScript-based chart generation logic.

## Architecture

### Technology Stack
- **Runtime**: Bun (fast all-in-one JavaScript runtime)
- **Language**: TypeScript with ESNext target
- **Module System**: ES Modules (type: "module")
- **Package Manager**: Bun (with bun.lock file)

### Project Structure
- **index.ts** - Main entry point (currently basic "Hello via Bun!" script)
- **tsconfig.json** - TypeScript configuration with strict settings and ESNext features
- **package.json** - Project metadata and dependencies
- **CLAUDE.md** - Existing Cursor rules for Bun development

## Development Commands

### Essential Commands
```bash
# Install dependencies
bun install

# Run the main script
bun run index.ts

# Run directly
bun index.ts

# Run with hot reload for development
bun --hot ./index.ts

# Run tests
bun test
```

### Building and Bundling
```bash
# Build TypeScript/JavaScript files
bun build <file>

# For frontend assets
bun build <file.html|file.ts|file.css>
```

## Development Guidelines

### Bun-Specific Practices
- Use `bun <file>` instead of `node <file>` or `ts-node <file>`
- Use `bun test` instead of `jest` or `vitest`
- Use `bun install` instead of `npm install` or `yarn install`
- Use `bun run <script>` instead of `npm run <script>`
- Bun automatically loads `.env` files - no need for dotenv

### API Preferences
- **HTTP Server**: Use `Bun.serve()` instead of Express
- **Database**: Use built-in `bun:sqlite`, `Bun.redis`, `Bun.sql`
- **WebSockets**: Built-in `WebSocket` instead of `ws`
- **File Operations**: Prefer `Bun.file` over `node:fs`
- **Shell Commands**: Use `Bun.$` instead of execa

### Testing
Use Bun's built-in test runner:

```typescript
import { test, expect } from "bun:test";

test("example test", () => {
  expect(1).toBe(1);
});
```

## Configuration

### TypeScript Settings
- **Target**: ESNext
- **Module**: Preserve (for bundler)
- **Strict Mode**: Enabled
- **JSX**: react-jsx support
- **Module Resolution**: bundler mode

### Dependencies
- **Development**: @types/bun
- **Peer**: TypeScript ^5

## Current Implementation Status

**State**: Basic scaffold/early development
- Simple "Hello, world!" entry point
- TypeScript configuration set up for modern ES features
- Bun-based development environment configured
- Ready for ECharts JavaScript execution implementation

**Expected Purpose**: Based on the parent echarts-convert plugin, this module likely handles:
- ECharts JavaScript code execution
- Chart rendering and conversion logic
- Server-side JavaScript processing for image generation

## Next Steps for Development

1. **Implement ECharts Execution Logic**
   - Add ECharts library dependencies
   - Create JavaScript execution sandbox
   - Implement chart rendering pipeline

2. **Add Image Generation**
   - Integrate with headless browser or canvas API
   - Support multiple output formats (PNG, JPEG, SVG)
   - Configure image dimensions and quality

3. **API Development**
   - Create HTTP endpoints for chart conversion
   - Implement request/response handling
   - Add error handling and validation

4. **Testing Setup**
   - Add test cases for ECharts conversion
   - Test various chart types and configurations
   - Performance testing for large charts