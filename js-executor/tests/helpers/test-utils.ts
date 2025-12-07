/**
 * Test utility functions for ECharts rendering tests
 */

import type { EChartsOption } from 'echarts'

/**
 * Load test fixture data
 */
export async function loadFixture<T>(filename: string): Promise<T> {
  const file = Bun.file(`tests/fixtures/${filename}`)
  return (await file.json()) as T
}

/**
 * Create test render options
 */
export function createTestRenderOptions(
  overrides: Partial<{
    width: number
    height: number
    mergeOptions?: EChartsOption
  }> = {}
) {
  return {
    width: 800,
    height: 600,
    ...overrides,
  }
}
