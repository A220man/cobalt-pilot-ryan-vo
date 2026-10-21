// PluginCard component
import { PluginListItem } from '../types'
import { formatDate, truncate, cn } from '../utils/cn'

interface PluginCardProps {
  plugin: PluginListItem
  onClick?: () => void
}

export function PluginCard({ plugin, onClick }: PluginCardProps) {
  const handleClick = () => {
    if (onClick) onClick()
  }

  return (
    <div
      className={cn(
        'bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700',
        'p-5 hover:border-emerald-300 dark:hover:border-emerald-700',
        'transition-all duration-200 cursor-pointer',
        onClick && 'hover:shadow-lg'
      )}
      onClick={handleClick}
    >
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
          <svg className="w-6 h-6 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="font-semibold text-slate-900 dark:text-slate-100 truncate">{plugin.name}</h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 truncate">{plugin.slug}</p>
            </div>
            {plugin.plugin_type && (
              <span className={cn(
                'px-2 py-0.5 text-xs font-medium rounded-full',
                plugin.plugin_type === 'official'
                  ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                  : 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
              )}>
                {plugin.plugin_type}
              </span>
            )}
          </div>
          {plugin.description && (
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300 line-clamp-2">
              {truncate(plugin.description, 200)}
            </p>
          )}
          <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
            <span className="flex items-center gap-1">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              {plugin.skills_count} skills
            </span>
            <span className="flex items-center gap-1">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" /></svg>
              {plugin.commands_count} commands
            </span>
            <span className="flex items-center gap-1">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
              {plugin.connectors_count} connectors
            </span>
            {plugin.updated_at && (
              <span>Updated {formatDate(plugin.updated_at)}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}