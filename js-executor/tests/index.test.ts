import { describe, it, expect, beforeEach, afterEach, spyOn } from 'bun:test'
import { parseCliOptions, renderChartsConcurrent } from '../index'
import type { EChartsOption } from 'echarts'

// A more advanced Mock Worker class for detailed testing
class MockWorker {
  receivedTasks: any[] = []
  onmessage: ((event: any) => void) | null = null
  onerror: ((event: any) => void) | null = null

  constructor(url: string) {
    // The mockWorkerInstances array is managed in the test setup
    mockWorkerInstances.push(this)
  }

  postMessage(task: any) {
    this.receivedTasks.push(task)
    setTimeout(() => {
      const mockResults = task.configs.map((config: any) => ({
        index: config.index,
        success: true,
        data: `worker-result-${config.index}`,
      }))
      if (this.onmessage) {
        this.onmessage({ data: { results: mockResults } })
      }
    }, 10)
  }

  terminate() {
    // Minimalist approach: only track calls, no side effects in the mock itself.
  }
}

let mockWorkerInstances: any[] = []
let originalWorker: any
let terminateSpy: any

beforeEach(() => {
  mockWorkerInstances = []
  // Spy on the prototype before any instances are created for this test
  terminateSpy = spyOn(MockWorker.prototype, 'terminate')
  originalWorker = global.Worker
  // @ts-ignore
  global.Worker = MockWorker
})

afterEach(() => {
  global.Worker = originalWorker
  terminateSpy.mockRestore() // Restore the spy to avoid conflicts between tests
})

describe('parseCliOptions', () => {
  const originalArgv = process.argv

  afterEach(() => {
    process.argv = originalArgv
  })

  it('should use default options when no arguments provided', () => {
    process.argv = ['bun', 'index.ts']
    const options = parseCliOptions()

    expect(options.width).toBe(800)
    expect(options.height).toBe(600)
    expect(options.concurrency).toBe(1)
    expect(options.mergeOptions).toBeUndefined()
  })

  it('should parse all CLI parameters correctly', () => {
    const mergeOptions = { animation: false, title: { text: 'Test' } }
    process.argv = [
      'bun',
      'index.ts',
      '--width',
      '1200',
      '--height',
      '800',
      '--concurrency',
      '4',
      '--merge-options',
      JSON.stringify(mergeOptions),
    ]

    const options = parseCliOptions()

    expect(options.width).toBe(1200)
    expect(options.height).toBe(800)
    expect(options.concurrency).toBe(4)
    expect(options.mergeOptions).toEqual(mergeOptions)
  })

  it('should exit with error for invalid JSON in merge-options', () => {
    process.argv = ['bun', 'index.ts', '--merge-options', '{invalid json}']

    const mockExit = spyOn(process, 'exit').mockImplementation(() => {
      throw new Error('process.exit called')
    })
    const mockError = spyOn(console, 'error').mockImplementation(() => {})

    expect(() => parseCliOptions()).toThrow('process.exit called')
    expect(mockError).toHaveBeenCalledWith(
      'Error: Invalid JSON for merge-options'
    )
    expect(mockExit).toHaveBeenCalledWith(1)

    mockExit.mockRestore()
    mockError.mockRestore()
  })
})

describe('renderChartsConcurrent', () => {
  it('should render sequentially when concurrency=1', async () => {
    const configs = [
      {
        index: 0,
        config: { series: [{ type: 'bar', data: [1, 2] }] } as EChartsOption,
      },
      {
        index: 1,
        config: { series: [{ type: 'line', data: [3, 4] }] } as EChartsOption,
      },
    ]

    const options = {
      width: 800,
      height: 600,
      concurrency: 1,
    }

    // Mock console.log to capture debug output
    const mockLog = spyOn(console, 'log').mockImplementation(() => {})

    const results = await renderChartsConcurrent(configs, options)

    expect(results).toHaveLength(2)
    // For concurrency=1, no debug messages about creating workers should appear
    const logCalls = mockLog.mock.calls.flat().join(' ')
    expect(logCalls).not.toContain('Creating worker')
    expect(logCalls).not.toContain('Worker created successfully')

    mockLog.mockRestore()
  })

  it('should create workers for concurrent rendering', async () => {
    const configs = [
      {
        index: 0,
        config: { series: [{ type: 'bar', data: [1, 2] }] } as EChartsOption,
      },
      {
        index: 1,
        config: { series: [{ type: 'line', data: [3, 4] }] } as EChartsOption,
      },
      {
        index: 2,
        config: { series: [{ type: 'pie', data: [5, 6] }] } as EChartsOption,
      },
    ]

    const options = {
      width: 1024,
      height: 768,
      concurrency: 2,
      mergeOptions: { animation: false } as EChartsOption,
    }

    const results = await renderChartsConcurrent(configs, options)

    expect(results).toHaveLength(3)

    // Verify results are in correct order and have mock data from workers
    expect(results[0]?.index).toBe(0)
    expect(results[0]?.data).toBe('worker-result-0')
    expect(results[1]?.index).toBe(1)
    expect(results[1]?.data).toBe('worker-result-1')
    expect(results[2]?.index).toBe(2)
    expect(results[2]?.data).toBe('worker-result-2')
  })

  it('should handle empty configs array', async () => {
    const configs: any[] = []
    const options = {
      width: 800,
      height: 600,
      concurrency: 2,
    }

    const results = await renderChartsConcurrent(configs, options)

    expect(results).toHaveLength(0)
  })

  it('should distribute configs across workers correctly', async () => {
    const configs = Array.from({ length: 6 }, (_: any, i: number) => ({
      index: i,
      config: { series: [{ type: 'bar', data: [i] }] } as EChartsOption,
    }))

    const options = {
      width: 800,
      height: 600,
      concurrency: 3,
    }

    const results = await renderChartsConcurrent(configs, options)

    expect(results).toHaveLength(6)

    // Verify all configs are processed and in correct order
    results.forEach((result, index) => {
      expect(result?.index).toBe(index)
    })
  })

  it('should maintain result order after concurrent processing', async () => {
    const configs = [
      { index: 5, config: { series: [{ type: 'bar' }] } as EChartsOption }, // Out of order
      { index: 2, config: { series: [{ type: 'line' }] } as EChartsOption },
      { index: 8, config: { series: [{ type: 'pie' }] } as EChartsOption },
    ]

    const options = {
      width: 800,
      height: 600,
      concurrency: 2,
    }

    const results = await renderChartsConcurrent(configs, options)

    expect(results).toHaveLength(3)
    // Results should be sorted by original index
    expect(results[0]?.index).toBe(2)
    expect(results[1]?.index).toBe(5)
    expect(results[2]?.index).toBe(8)
  })

  it('should terminate all workers after completion', async () => {
    const configs = Array.from({ length: 5 }, (_, i) => ({
      index: i,
      config: { series: [{ type: 'bar' }] } as EChartsOption,
    }))
    const options = { width: 800, height: 600, concurrency: 4 }

    await renderChartsConcurrent(configs, options)

    // Should create 4 workers for 5 tasks with concurrency 4
    expect(mockWorkerInstances.length).toBe(4)
    // And all of them should be terminated
    expect(terminateSpy).toHaveBeenCalledTimes(4)
  })

  it('should distribute tasks unevenly when task count is not a multiple of concurrency', async () => {
    const configs = Array.from({ length: 7 }, (_, i) => ({
      index: i,
      config: { series: [{ type: 'bar' }] } as EChartsOption,
    }))
    const options = { width: 800, height: 600, concurrency: 3 }

    await renderChartsConcurrent(configs, options)

    // Should create 3 workers
    expect(mockWorkerInstances.length).toBe(3)

    // Distribution should be 3, 2, 2 for 7 tasks
    const taskLengths = mockWorkerInstances.map(
      (w) => w.receivedTasks[0].configs.length
    )
    expect(taskLengths.sort((a, b) => b - a)).toEqual([3, 2, 2])
  })

  it('should only create as many workers as there are tasks if tasks < concurrency', async () => {
    const configs = Array.from({ length: 2 }, (_, i) => ({
      index: i,
      config: { series: [{ type: 'bar' }] } as EChartsOption,
    }))
    const options = { width: 800, height: 600, concurrency: 5 }

    await renderChartsConcurrent(configs, options)

    // Should only create 2 workers, not 5
    expect(mockWorkerInstances.length).toBe(2)
    expect(terminateSpy).toHaveBeenCalledTimes(2)

    // Each worker gets 1 task
    const taskLengths = mockWorkerInstances.map(
      (w) => w.receivedTasks[0].configs.length
    )
    expect(taskLengths).toEqual([1, 1])
  })
})
