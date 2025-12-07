/**
 * Type definitions for testing
 */

import type { EChartsOption } from 'echarts';

/**
 * Test fixture data structure, used in valid-configs.json
 */
export interface TestFixtures {
  barChart: EChartsOption;
  lineChart: EChartsOption;
  pieChart: EChartsOption;
}