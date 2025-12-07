// Worker thread for batch rendering ECharts charts
// This runs in a separate thread for true concurrent execution

declare var self: Worker;

import type { EChartsOption } from 'echarts';
import { renderChart, type RenderOptions, type RenderResult } from './render';

// Message types
interface ChartConfig {
  index: number;
  config: EChartsOption;
}

interface BatchRenderTask {
  configs: ChartConfig[];
  width: number;
  height: number;
  mergeOptions?: EChartsOption;
}

interface BatchRenderResponse {
  results: RenderResult[];
}

// Handle batch render requests
self.onmessage = async (event: MessageEvent<BatchRenderTask>) => {
  const task = event.data;
  const results: RenderResult[] = [];

  // Process each chart configuration in the batch
  const renderOptions: RenderOptions = {
    width: task.width,
    height: task.height,
    mergeOptions: task.mergeOptions
  };

  for (const chartConfig of task.configs) {
    const result = renderChart(chartConfig.config, renderOptions, chartConfig.index);
    results.push(result);
  }

  // Send batch results back
  const response: BatchRenderResponse = {
    results
  };

  postMessage(response);
};