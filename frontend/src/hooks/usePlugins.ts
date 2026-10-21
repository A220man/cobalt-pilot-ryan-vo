// React hooks for plugin data
import { useState, useEffect, useCallback } from 'react'
import { api } from '../api/client'
import type {
  PluginListItem,
  PluginDetail,
  Skill,
  PaginatedResponse,
  SyncLog,
  PluginStats,
  StabilityLevel,
  PluginType,
} from '../types'

export function usePlugins(params?: {
  page?: number
  page_size?: number
  search?: string
  plugin_type?: PluginType
}) {
  const [data, setData] = useState<PaginatedResponse<PluginListItem> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await api.listPlugins(params)
      setData(result)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch plugins')
    } finally {
      setLoading(false)
    }
  }, [params?.page, params?.page_size, params?.search, params?.plugin_type])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { data, loading, error, refetch: fetch }
}

export function usePlugin(slug: string | undefined) {
  const [data, setData] = useState<PluginDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetch = useCallback(async () => {
    if (!slug) return
    setLoading(true)
    setError(null)
    try {
      const result = await api.getPlugin(slug)
      setData(result)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch plugin')
    } finally {
      setLoading(false)
    }
  }, [slug])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { data, loading, error, refetch: fetch }
}

export function usePluginStats() {
  const [data, setData] = useState<PluginStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await api.getPluginStats()
      setData(result)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch stats')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { data, loading, error, refetch: fetch }
}

export function useSyncPlugins() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<SyncLog | null>(null)

  const sync = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await api.syncPlugins()
      setResult(res)
      return res
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Sync failed')
      throw e
    } finally {
      setLoading(false)
    }
  }, [])

  return { sync, loading, error, result }
}

export function usePluginSkills(
  pluginSlug: string | undefined,
  params?: {
    page?: number
    page_size?: number
    stability?: StabilityLevel
    search?: string
  }
) {
  const [data, setData] = useState<PaginatedResponse<Skill> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetch = useCallback(async () => {
    if (!pluginSlug) return
    setLoading(true)
    setError(null)
    try {
      const result = await api.listPluginSkills(pluginSlug, params)
      setData(result)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch skills')
    } finally {
      setLoading(false)
    }
  }, [pluginSlug, params?.page, params?.page_size, params?.stability, params?.search])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { data, loading, error, refetch: fetch }
}