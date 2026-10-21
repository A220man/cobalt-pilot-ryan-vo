// API client
import axios, { AxiosInstance, AxiosError } from 'axios'
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

const API_BASE = (import.meta as any).env?.VITE_API_BASE || '/api'

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<any>) => {
        const message = error.response?.data?.detail || error.message
        return Promise.reject(new Error(message))
      }
    )
  }

  async healthCheck() {
    const response = await this.client.get<{ status: string; version: string }>('/health')
    return response.data
  }

  async listPlugins(params?: {
    page?: number
    page_size?: number
    search?: string
    plugin_type?: PluginType
  }): Promise<PaginatedResponse<PluginListItem>> {
    const response = await this.client.get<PaginatedResponse<PluginListItem>>('/plugins', { params })
    return response.data
  }

  async getPluginStats(): Promise<PluginStats> {
    const response = await this.client.get<PluginStats>('/plugins/stats')
    return response.data
  }

  async syncPlugins(): Promise<SyncLog> {
    const response = await this.client.post<SyncLog>('/plugins/sync')
    return response.data
  }

  async getPlugin(slug: string): Promise<PluginDetail> {
    const response = await this.client.get<PluginDetail>(`/plugins/${slug}`)
    return response.data
  }

  async listPluginSkills(
    pluginSlug: string,
    params?: {
      page?: number
      page_size?: number
      stability?: StabilityLevel
      search?: string
    }
  ): Promise<PaginatedResponse<Skill>> {
    const response = await this.client.get<PaginatedResponse<Skill>>(`/plugins/${pluginSlug}/skills`, { params })
    return response.data
  }

  async getSkill(pluginSlug: string, skillSlug: string): Promise<Skill> {
    const response = await this.client.get<Skill>(`/plugins/${pluginSlug}/skills/${skillSlug}`)
    return response.data
  }
}

export const api = new ApiClient()