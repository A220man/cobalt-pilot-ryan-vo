// PluginDetailPage
import { useParams, Link } from 'react-router-dom'
import { usePlugin, usePluginSkills } from '../hooks/usePlugins'
import { StabilityBadge } from '../components'
import { cn, formatDate, truncate } from '../utils/cn'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export function PluginDetailPage() {
  const { slug } = useParams<{ slug: string }>()
  const { data: plugin, loading, error } = usePlugin(slug)
  const [activeTab, setActiveTab] = useState<'skills' | 'commands' | 'connectors' | 'readme'>('skills')
  const [stabilityFilter, setStabilityFilter] = useState<string>('')
  const [skillPage, setSkillPage] = useState(1)

  const { data: skillsData, loading: skillsLoading } = usePluginSkills(slug, {
    page: skillPage,
    page_size: 20,
    stability: stabilityFilter as any || undefined,
  })

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-emerald-500 border-t-transparent" />
      </div>
    )
  }

  if (error || !plugin) {
    return (
      <div className="text-center py-12 text-red-600 dark:text-red-400">
        <p>Failed to load plugin: {error || 'Not found'}</p>
        <Link to="/plugins" className="mt-4 inline-block text-emerald-600 hover:underline">
          ← Back to plugins
        </Link>
      </div>
    )
  }

  const tabs = [
    { id: 'skills', label: `Skills (${plugin.skills.length})`, count: plugin.skills.length },
    { id: 'commands', label: `Commands (${plugin.commands.length})`, count: plugin.commands.length },
    { id: 'connectors', label: `Connectors (${plugin.connectors.length})`, count: plugin.connectors.length },
    { id: 'readme', label: 'README', count: 0 },
  ] as const

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <Link to="/plugins" className="text-sm text-slate-500 dark:text-slate-400 hover:underline mb-2 inline-block">
            ← All Plugins
          </Link>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">{plugin.name}</h1>
            {plugin.plugin_type && (
              <span className={cn(
                'px-3 py-1 text-sm font-medium rounded-full',
                plugin.plugin_type === 'official'
                  ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                  : 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
              )}>
                {plugin.plugin_type}
              </span>
            )}
          </div>
          <p className="mt-2 text-slate-600 dark:text-slate-400 max-w-3xl">{plugin.description || 'No description available.'}</p>
          <div className="mt-3 flex flex-wrap items-center gap-4 text-sm text-slate-500 dark:text-slate-400">
            <span>Updated {formatDate(plugin.updated_at)}</span>
            {plugin.license && <span>License: {plugin.license}</span>}
            {plugin.repo_path && <span>Path: {plugin.repo_path}</span>}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200 dark:border-slate-700">
        <nav className="flex gap-1" aria-label="Plugin sections">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'px-4 py-3 text-sm font-medium border-b-2 transition-colors',
                activeTab === tab.id
                  ? 'border-emerald-500 text-emerald-600 dark:text-emerald-400'
                  : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
              )}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="space-y-4">
        {activeTab === 'skills' && (
          <div className="space-y-4">
            {/* Stability filter */}
            <div className="flex items-center gap-3">
              <label className="text-sm text-slate-500 dark:text-slate-400">Filter by stability:</label>
              <select
                value={stabilityFilter}
                onChange={(e) => {
                  setStabilityFilter(e.target.value)
                  setSkillPage(1)
                }}
                className="px-3 py-2 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-lg text-sm"
              >
                <option value="">All</option>
                <option value="stable">Stable</option>
                <option value="experimental">Experimental</option>
                <option value="deprecated">Deprecated</option>
              </select>
            </div>

            {skillsLoading ? (
              <div className="flex items-center justify-center h-48">
                <div className="animate-spin rounded-full h-8 w-8 border-3 border-emerald-500 border-t-transparent" />
              </div>
            ) : skillsData?.items.length === 0 ? (
              <div className="text-center py-8 text-slate-500 dark:text-slate-400">
                <p>No skills found</p>
              </div>
            ) : (
              <>
                <div className="space-y-3">
                  {skillsData?.items.map((skill) => (
                    <SkillCard key={skill.id} skill={skill} />
                  ))}
                </div>

                {skillsData && skillsData.total_pages > 1 && (
                  <div className="flex items-center justify-center gap-2 mt-4">
                    <button
                      onClick={() => setSkillPage(p => Math.max(1, p - 1))}
                      disabled={skillPage === 1}
                      className="px-3 py-1.5 text-sm border border-slate-300 dark:border-slate-600 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-50"
                    >
                      Previous
                    </button>
                    <span className="px-4 text-sm text-slate-600 dark:text-slate-400">
                      Page {skillPage} of {skillsData.total_pages}
                    </span>
                    <button
                      onClick={() => setSkillPage(p => Math.min(skillsData.total_pages, p + 1))}
                      disabled={skillPage === skillsData.total_pages}
                      className="px-3 py-1.5 text-sm border border-slate-300 dark:border-slate-600 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 disabled:opacity-50"
                    >
                      Next
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {activeTab === 'commands' && (
          <div className="space-y-3">
            {plugin.commands.length === 0 ? (
              <div className="text-center py-8 text-slate-500 dark:text-slate-400">No commands available</div>
            ) : (
              plugin.commands.map((cmd) => (
                <CommandCard key={cmd.id} command={cmd} />
              ))
            )}
          </div>
        )}

        {activeTab === 'connectors' && (
          <div className="space-y-3">
            {plugin.connectors.length === 0 ? (
              <div className="text-center py-8 text-slate-500 dark:text-slate-400">No connectors configured</div>
            ) : (
              plugin.connectors.map((conn) => (
                <ConnectorCard key={conn.id} connector={conn} />
              ))
            )}
          </div>
        )}

        {activeTab === 'readme' && (
          <div className="prose prose-slate dark:prose-invert max-w-none p-4">
            {plugin.readme_content ? (
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{plugin.readme_content}</ReactMarkdown>
            ) : (
              <p className="text-slate-500 dark:text-slate-400">No README available</p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// SkillCard component
function SkillCard({ skill }: { skill: any }) {
  return (
    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-4 hover:border-emerald-300 dark:hover:border-emerald-700 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h4 className="font-semibold text-slate-900 dark:text-slate-100">{skill.name}</h4>
            <StabilityBadge stability={skill.stability} size="sm" />
          </div>
          {skill.markdown_content && (
            <div className="mt-3 prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{skill.markdown_content}</ReactMarkdown>
            </div>
          )}
          {skill.frontmatter && Object.keys(skill.frontmatter).length > 0 && (
            <div className="mt-2 text-xs text-slate-500 dark:text-slate-400 font-mono">
              {JSON.stringify(skill.frontmatter, null, 2)}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// CommandCard component
function CommandCard({ command }: { command: any }) {
  return (
    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <code className="px-2 py-0.5 bg-slate-100 dark:bg-slate-800 rounded text-sm font-mono text-emerald-600 dark:text-emerald-400">
              /{command.slug}
            </code>
            <h4 className="font-semibold text-slate-900 dark:text-slate-100">{command.name}</h4>
          </div>
          {command.description && <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{truncate(command.description, 300)}</p>}
        </div>
      </div>
    </div>
  )
}

// ConnectorCard component
function ConnectorCard({ connector }: { connector: any }) {
  return (
    <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            {connector.name}
            {connector.type && (
              <span className="px-2 py-0.5 text-xs bg-slate-100 dark:bg-slate-800 rounded text-slate-600 dark:text-slate-400">
                {connector.type}
              </span>
            )}
          </h4>
          {connector.description && <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{truncate(connector.description, 300)}</p>}
          {connector.config && (
            <details className="mt-2">
              <summary className="text-xs text-slate-500 dark:text-slate-400 cursor-pointer">View config</summary>
              <pre className="mt-2 p-2 bg-slate-50 dark:bg-slate-900 rounded text-xs overflow-auto max-h-40">
                {JSON.stringify(connector.config, null, 2)}
              </pre>
            </details>
          )}
        </div>
      </div>
    </div>
  )
}

import { useState } from 'react'