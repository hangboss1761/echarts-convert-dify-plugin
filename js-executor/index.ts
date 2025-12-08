#!/usr/bin/env bun

import type { EChartsOption } from 'echarts';
import { renderChart, type RenderOptions, type RenderResult } from './render';

// CLI options interface
export interface CliOptions {
  width: number;
  height: number;
  concurrency: number;
  mergeOptions?: EChartsOption;
}

// Input chart configuration interface
export interface ChartConfig {
  index: number;
  config: EChartsOption;
}

// Parse CLI arguments
export function parseCliOptions(): CliOptions {
  const args = process.argv.slice(2);
  const options: CliOptions = {
    width: 800,
    height: 600,
    concurrency: 1
  };

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    switch (arg) {
      case '--width':
        const widthValue = args[++i];
        if (widthValue) {
          options.width = parseInt(widthValue);
        }
        break;
      case '--height':
        const heightValue = args[++i];
        if (heightValue) {
          options.height = parseInt(heightValue);
        }
        break;
      case '--concurrency':
        const concurrencyValue = args[++i];
        if (concurrencyValue) {
          options.concurrency = parseInt(concurrencyValue);
        }
        break;
      case '--merge-options':
        const mergeOptionsValue = args[++i];
        if (mergeOptionsValue) {
          try {
            options.mergeOptions = JSON.parse(mergeOptionsValue);
          } catch (e) {
            console.error('Error: Invalid JSON for merge-options');
            process.exit(1);
          }
        }
        break;
    }
  }

  return options;
}

// Concurrent rendering using Worker threads
export async function renderChartsConcurrent(
  configs: ChartConfig[],
  options: CliOptions
): Promise<RenderResult[]> {
  if (options.concurrency <= 1) {
    // Sequential rendering
    return configs.map(config => {
      const renderOptions: RenderOptions = {
        width: options.width,
        height: options.height,
        mergeOptions: options.mergeOptions
      };
      return renderChart(config.config, renderOptions, config.index);
    });
  }

  // Determine optimal number of workers
  const workerCount = Math.min(options.concurrency, configs.length);
  const chunkSize = Math.ceil(configs.length / workerCount);

  // Split configs into chunks for worker processing using round-robin distribution
  const chunks: ChartConfig[][] = Array.from({ length: workerCount }, () => []);
  for (let i = 0; i < configs.length; i++) {
    chunks[i % workerCount]?.push(configs[i]!);
  }

  // Create workers and assign chunks
  const workerPromises = chunks.map(async (chunk, workerIndex) => {
    return new Promise<RenderResult[]>((resolve, reject) => {
      // Create worker for this chunk using Bun's syntax
      const worker = new Worker('./worker.ts');

      // Send batch render task to worker
      const task = {
        configs: chunk,
        width: options.width,
        height: options.height,
        mergeOptions: options.mergeOptions
      };

      worker.postMessage(task);

      // Handle worker response
      worker.onmessage = (event) => {
        const response = event.data;
        worker.terminate();
        resolve(response.results);
      };

      worker.onerror = (error) => {
        worker.terminate();
        reject(new Error(`Worker ${workerIndex} error: ${error.message}`));
      };
    });
  });

  // Wait for all workers to complete
  const chunkResults = await Promise.all(workerPromises);

  // Flatten all results and maintain original order
  const allResults: RenderResult[] = [];
  chunkResults.forEach(chunkResult => {
    allResults.push(...chunkResult);
  });

  // Sort results by index to maintain original order
  allResults.sort((a, b) => {
    if (a.index === undefined || b.index === undefined) return 0;
    return a.index - b.index;
  });

  return allResults;
}

// Main function
async function main(): Promise<void> {
  try {
    const options = parseCliOptions();

    // Read JSON array from stdin
    let inputData = '';
    for await (const chunk of process.stdin) {
      inputData += chunk;
    }

    if (!inputData.trim()) {
      console.error('Error: No input data provided via stdin');
      process.exit(1);
    }

    // Parse JSON array of ECharts configurations
    const configs: EChartsOption[] = JSON.parse(inputData);
    if (!Array.isArray(configs)) {
      console.error('Error: Input must be a JSON array');
      process.exit(1);
    }

    // Add index to each config for tracking
    const chartConfigs: ChartConfig[] = configs.map((config, index) => ({
      index,
      config
    }));

    // Render charts
    const results = await renderChartsConcurrent(chartConfigs, options);

    // Output results as JSON
    console.log(JSON.stringify({ results }));

  } catch (error) {
    console.error(JSON.stringify({
      error: (error as Error).message
    }));
    process.exit(1);
  }
}

// Run main function only when this file is executed directly
if (require.main === module) {
  main();
}