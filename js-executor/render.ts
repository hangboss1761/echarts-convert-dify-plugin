// Shared rendering logic for ECharts charts
// Used by both main thread and worker threads

import * as echarts from 'echarts';
import merge from 'lodash.merge';
import type { EChartsOption } from 'echarts';

export type { EChartsOption };

export interface RenderOptions {
  width: number;
  height: number;
  mergeOptions?: EChartsOption;
}

export interface RenderResult {
  success: boolean;
  data?: string; // base64 encoded SVG
  error?: string;
  index?: number;
}

/**
 * Render a single ECharts configuration to SVG
 *
 * @param config - ECharts configuration
 * @param options - Rendering options (width, height, mergeOptions)
 * @param index - Optional index for tracking
 * @returns RenderResult with base64 encoded SVG or error
 */
export function renderChart(
  config: EChartsOption | null | undefined,
  options: RenderOptions,
  index?: number
): RenderResult {
  try {
    if (!config) {
      throw new Error('Chart configuration is null or undefined.');
    }

    // Initialize chart with SVG renderer
    const chart = echarts.init(null, null, {
      renderer: 'svg',
      ssr: true,
      width: options.width,
      height: options.height,
    });

    // Merge configurations with merge options taking priority
    let finalConfig = config;
    if (options.mergeOptions) {
      finalConfig = merge({}, config, options.mergeOptions);
    }

    chart.setOption(finalConfig);
    const svgStr = chart.renderToSVGString();
    chart.dispose();

    // Convert to base64
    const svgBuffer = Buffer.from(svgStr, 'utf8');
    const chartBase64 = `data:image/svg+xml;base64,${svgBuffer.toString('base64')}`;

    return {
      success: true,
      data: chartBase64,
      index
    };

  } catch (error) {
    return {
      success: false,
      error: (error as Error).message,
      index
    };
  }
}