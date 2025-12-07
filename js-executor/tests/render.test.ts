/**
 * Unit tests for render.ts
 */

import { describe, it, expect, beforeEach } from 'bun:test';
import { renderChart } from '../render';
import { loadFixture, createTestRenderOptions } from './helpers/test-utils';
import type { TestFixtures } from './types/test-types';

describe('renderChart', () => {
  let fixtures: TestFixtures;

  beforeEach(async () => {
    fixtures = await loadFixture<TestFixtures>('valid-configs.json') as TestFixtures;
  });

  describe('Basic Rendering', () => {
    it('should render bar, line, and pie charts', () => {
      const configs = [fixtures.barChart, fixtures.lineChart, fixtures.pieChart];
      const options = createTestRenderOptions();

      const results = configs.map((config, index) =>
        renderChart(config, options, index)
      );

      // All should succeed and return a valid base64 svg
      results.forEach((result, index) => {
        expect(result.success).toBe(true);
        expect(result.data).toStartWith('data:image/svg+xml;base64,');
        expect(result.index).toBe(index);
      });
    });

    it('should return correct result format on success', () => {
      const result = renderChart(fixtures.barChart, createTestRenderOptions(), 0);

      expect(result.success).toBe(true);
      expect(result.data).toBeString();
      expect(result.index).toBe(0);
      expect(result.error).toBeUndefined();
    });
  });

  describe('Configuration Processing', () => {
    it('should handle empty and null configurations', () => {
      // An empty config is still valid and should produce a blank chart
      const emptyResult = renderChart({}, createTestRenderOptions());
      expect(emptyResult.success).toBe(true);
      expect(emptyResult.data).toStartWith('data:image/svg+xml;base64,');

      // A null config should now result in a controlled error
      const nullResult = renderChart(null, createTestRenderOptions());
      expect(nullResult.success).toBe(false);
      expect(nullResult.error).toBe('Chart configuration is null or undefined.');
    });
  });

  describe('SVG Output', () => {
    it('should respect specified dimensions', () => {
      const testWidth = 1024;
      const testHeight = 768;
      const options = createTestRenderOptions({ width: testWidth, height: testHeight });
      const result = renderChart(fixtures.barChart, options);

      expect(result.success).toBe(true);
      const svgContent = Buffer.from(result.data!.split(',')[1]!, 'base64').toString('utf-8');

      // A simple check is enough, as ECharts handles the rendering
      expect(svgContent).toContain(`width="${testWidth}"`);
      expect(svgContent).toContain(`height="${testHeight}"`);
    });
  });
});