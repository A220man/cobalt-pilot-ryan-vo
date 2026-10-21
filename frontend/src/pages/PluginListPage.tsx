// PluginList page
import { useState } from 'react'
import { usePlugins, usePluginStats } from '../hooks/usePlugins'
import { PluginCard, SearchInput, SyncButton, Button } from '../components'
import { PluginType } from '../types'

export function PluginListPage() {
  const [search, setSearch] = useState('')
  const [pluginType, setPluginType] = useState<PluginType | ''>('')
  const [page, setPage] = useState(1)
  const pageSize = 12

  const { data, loading, error, refetch } = usePlugins({ page, page_size: pageSize, search, plugin_type: pluginType || undefined })
  const { data: stats } = usePluginStats()

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value)
    setPage(1)
  }

  const handleTypeChange = (type: PluginType | '') => {
    setPluginType(type)
    setPage(1)
  }

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-emerald-500 border-t-transparent" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12 text-red-600 dark:text-red-400">
        <p>Failed to load plugins: {error}</p>
        <button onClick={refetch} className="mt-4 text-emerald-600 hover:underline">Retry</button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with stats and sync */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Plugins</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Discover plugins for Claude Cowork from the official knowledge-work-plugins repository
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <SyncButton />
          {stats && (
            <div className="flex items-center gap-4 text-sm text-slate-500 dark:text-slate-400">
              <span>{stats.total_plugins} plugins</span>
              <span>{stats.total_skills} skills</span>
              <span>{stats.total_commands} commands</span>
              <span>{stats.total_connectors} connectors</span>
            </div>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <SearchInput
          value={search}
          onChange={handleSearch}
          placeholder="Search by name, description, or slug..."
          className="max-w-md"
        />
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-500 dark:text-slate-400">Type:</label>
          <select
            value={pluginType}
            onChange={(e) => handleTypeChange(e.target.value as PluginType | '')}
            className="px-3 py-2 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-lg text-sm text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">All Types</option>
            <option value="official">Official</option>
            <option value="community">Community</option>
          </select>
        </div>
      </div>

      {/* Plugin Grid */}
      {data?.items.length === 0 ? (
        <div className="text-center py-12 text-slate-500 dark:text-slate-400">
          <svg className="mx-auto h-12 w-12 text-slate-300 dark:text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="mt-4 text-lg">No plugins found</p>
          <p className="mt-1">Try adjusting your search or filters</p>
        </div>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {data?.items.map((plugin) => (
              <PluginCard
                key={plugin.id}
                plugin={plugin}
                onClick={() => window.location.href = `/plugins/${plugin.slug}`}
              />
            ))}
          </div>

          {/* Pagination */}
          {data && data.total_pages > 1 && (
            <div className="flex items-center justify-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                Previous
              </Button>
              <span className="px-4 text-sm text-slate-600 dark:text-slate-400">
                Page {page} of {data.total_pages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(p => Math.min(data.total_pages, p + 1))}
                disabled={page === data.total_pages}
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}