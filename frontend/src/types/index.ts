// Frontend types matching backend schemas

export type PluginType = 'official' | 'community'
export type StabilityLevel = 'experimental' | 'stable' | 'deprecated'
export type SyncStatus = 'started' | 'success' | 'failed' | 'partial'

export interface Connector {
  id: number
  name: string
  type?: string
  config?: Record<string, any>
  description?: string
  created_at: string
  updated_at: string
}

export interface Command {
  id: number
  slug: string
  name: string
  description?: string
  markdown_content?: string
  file_path?: string
  created_at: string
  updated_at: string
}

export interface Skill {
  id: number
  slug: string
  name: string
  description?: string
  stability: StabilityLevel
  markdown_content?: string
  frontmatter?: Record<string, any>
  file_path?: string
  created_at: string
  updated_at: string
  plugin_slug?: string
  plugin_name?: string
}

export interface PluginListItem {
  id: number
  slug: string
  name: string
  description?: string
  plugin_type: PluginType
  repo_path?: string
  readme_content?: string
  license?: string
  created_at: string
  updated_at: string
  skills_count: number
  commands_count: number
  connectors_count: number
}

export interface PluginDetail extends PluginListItem {
  skills: Skill[]
  commands: Command[]
  connectors: Connector[]
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface SyncLog {
  id: number
  status: SyncStatus
  plugins_synced: number
  skills_synced: number
  commands_synced: number
  connectors_synced: number
  error_message?: string
  started_at: string
  completed_at?: string
}

export interface PluginStats {
  total_plugins: number
  total_skills: number
  total_commands: number
  total_connectors: number
  stability_distribution: Record<string, number>
}


export type LLMProvider = 'openai-compatible' | 'anthropic' | 'gemini' | 'ollama'

export interface LLMExplanationRequest {
  skill_slug: string
  plugin_slug: string
  question?: string
  context?: string
}

export interface LLMExplanationResponse {
  explanation: string
  provider: string
  model: string
  advisory: boolean
  disclaimer: string
}

export interface LLMConfig {
  provider: LLMProvider
  model: string
  base_url?: string
  has_api_key: boolean
  timeout_seconds: number
}

export interface LLMExplanationLog {
  id: number
  skill_slug: string
  plugin_slug: string
  provider: string
  model: string
  question?: string
  response_preview?: string
  created_at: string
}