// Hook tests
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { usePlugins, usePluginStats, useSyncPlugins } from '../hooks/usePlugins'
import type { PaginatedResponse, PluginListItem, PluginStats, SyncLog } from '../types'
import { api } from '../api/client'

describe('usePlugins', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches plugins on mount', async () => {
    const mockData: PaginatedResponse<PluginListItem> = {
      items: [{ id: 1, slug: 'p1', name: 'Plugin 1', plugin_type: 'official', skills_count: 0, commands_count: 0, connectors_count: 0, created_at: '', updated_at: '' }],
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1,
    }
    vi.spyOn(api, 'listPlugins').mockResolvedValue(mockData)

    const { result } = renderHook(() => usePlugins({ page: 1, page_size: 20 }))

    await waitFor(() => expect(result.current.loading).toBe(false))
    
    expect(result.current.data).toEqual(mockData)
    expect(result.current.error).toBeNull()
    expect(api.listPlugins).toHaveBeenCalledWith({ page: 1, page_size: 20, search: undefined, plugin_type: undefined })
  })

  it('handles fetch error', async () => {
    vi.spyOn(api, 'listPlugins').mockRejectedValue(new Error('Network error'))

    const { result } = renderHook(() => usePlugins())

    await waitFor(() => expect(result.current.loading).toBe(false))
    
    expect(result.current.error).toBe('Network error')
    expect(result.current.data).toBeNull()
  })

  it('refetches when params change', async () => {
    const mockData1: PaginatedResponse<PluginListItem> = {
      items: [{ id: 1, slug: 'p1', name: 'Plugin 1', plugin_type: 'official', skills_count: 0, commands_count: 0, connectors_count: 0, created_at: '', updated_at: '' }],
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1,
    }
    const mockData2: PaginatedResponse<PluginListItem> = {
      items: [{ id: 2, slug: 'p2', name: 'Plugin 2', plugin_type: 'official', skills_count: 0, commands_count: 0, connectors_count: 0, created_at: '', updated_at: '' }],
      total: 1,
      page: 2,
      page_size: 20,
      total_pages: 1,
    }
    vi.spyOn(api, 'listPlugins')
      .mockResolvedValueOnce(mockData1)
      .mockResolvedValueOnce(mockData2)

    const { result, rerender } = renderHook(
      ({ page }) => usePlugins({ page, page_size: 20 }),
      { initialProps: { page: 1 } }
    )

    await waitFor(() => expect(result.current.loading).toBe(false))
    
    rerender({ page: 2 })
    
    await waitFor(() => expect(result.current.loading).toBe(false))
    
    expect(api.listPlugins).toHaveBeenCalledTimes(2)
  })
})

describe('usePluginStats', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('fetches stats on mount', async () => {
    const mockStats: PluginStats = {
      total_plugins: 11,
      total_skills: 100,
      total_commands: 50,
      total_connectors: 30,
      stability_distribution: { stable: 50, experimental: 40, deprecated: 10 },
    }
    vi.spyOn(api, 'getPluginStats').mockResolvedValue(mockStats)

    const { result } = renderHook(() => usePluginStats())

    await waitFor(() => expect(result.current.loading).toBe(false))
    
    expect(result.current.data).toEqual(mockStats)
    expect(result.current.error).toBeNull()
  })
})

describe('useSyncPlugins', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('syncs and returns result', async () => {
    const mockResult: SyncLog = {
      id: 1,
      status: 'success',
      plugins_synced: 11,
      skills_synced: 100,
      commands_synced: 50,
      connectors_synced: 30,
      started_at: '2024-01-01T00:00:00Z',
      completed_at: '2024-01-01T00:01:00Z',
    }
    vi.spyOn(api, 'syncPlugins').mockResolvedValue(mockResult)

    const { result } = renderHook(() => useSyncPlugins())

    await act(async () => {
      await result.current.sync()
    })

    expect(result.current.loading).toBe(false)
    expect(result.current.result).toEqual(mockResult)
    expect(result.current.error).toBeNull()
  })

  it('handles sync error', async () => {
    vi.spyOn(api, 'syncPlugins').mockRejectedValue(new Error('Sync failed'))

    const { result } = renderHook(() => useSyncPlugins())

    await act(async () => {
      try {
        await result.current.sync()
      } catch {
        // Expected
      }
    })

    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBe('Sync failed')
    expect(result.current.result).toBeNull()
  })
})