
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

const API_BASE = (import.meta as unknown).env?.VITE_API_BASE || '/api'

let authToken: string | null = null

export function setAuthToken(token: string | null) {
  authToken = token
}

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

    this.client.interceptors.request.use((config) => {
      if (authToken) {
        config.headers.Authorization = `Bearer ${authToken}`
      }
      return config
    })

    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<unknown>) => {
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

  // Auth endpoints
  async getAuthUrl(redirectUri: string) {
    const response = await this.client.get<{ auth_url: string; state: string; nonce: string }>('/auth/login', {
      params: { redirect_uri: redirectUri }
    })
    return response.data
  }

  async exchangeCode(code: string, state: string, nonce: string) {
    const response = await this.client.post<{ access_token: string; token_type: string; expires_in: number; refresh_token?: string }>(
      '/auth/callback',
      { code, state, nonce }
    )
    return response.data
  }

  async logout(redirectUri: string) {
    const response = await this.client.post<{ logout_url: string }>('/auth/logout', null, {
      params: { redirect_uri: redirectUri }
    })
    return response.data
  }

  async getMe() {
    const response = await this.client.get<{
      id: string
      email: string | null
      username: string | null
      full_name: string | null
      roles: string[]
      is_active: boolean
      is_superuser: boolean
    }>('/auth/me')
    return response.data
  }

  async refreshToken() {
    const response = await this.client.post<{ access_token: string; token_type: string; expires_in: number; refresh_token?: string }>('/auth/refresh')
    return response.data
  }

  async testViewerAccess() {
    const response = await this.client.get<{ message: string }>('/auth/test/viewer')
    return response.data
  }

  async testOperatorAccess() {
    const response = await this.client.get<{ message: string }>('/auth/test/operator')
    return response.data
  }

  async testAdminAccess() {
    const response = await this.client.get<{ message: string }>('/auth/test/admin')
    return response.data
  }
}

export const api = new ApiClient()
