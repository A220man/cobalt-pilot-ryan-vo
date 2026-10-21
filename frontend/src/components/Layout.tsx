// Layout component
import { Outlet, Link } from 'react-router-dom'

export function Layout({ children }: { children?: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors">
      <header className="border-b border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/plugins" className="flex items-center gap-2 text-xl font-bold text-slate-900 dark:text-slate-100 hover:opacity-80 transition-opacity">
              <svg className="w-8 h-8 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 32 32">
                <rect width="32" height="32" rx="6" fill="#1a1a2e"/>
                <path d="M8 12h16M8 16h12M8 20h8" stroke="#00d4aa" strokeWidth="2.5" strokeLinecap="round"/>
                <circle cx="24" cy="20" r="4" fill="#00d4aa"/>
              </svg>
              <span>Cobalt Pilot</span>
            </Link>
            <nav className="flex items-center gap-4">
              <Link
                to="/plugins"
                className="text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors"
              >
                Plugins
              </Link>
              <a
                href="https://github.com/anthropics/knowledge-work-plugins"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors"
              >
                GitHub
              </a>
            </nav>
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children ?? <Outlet />}
      </main>
      <footer className="border-t border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-slate-500 dark:text-slate-400">
            Cobalt Pilot — Plugin Discovery for Claude Cowork
            <br />
            Data sourced from <a href="https://github.com/anthropics/knowledge-work-plugins" target="_blank" rel="noopener noreferrer" className="underline hover:text-emerald-600">anthropics/knowledge-work-plugins</a>
          </p>
        </div>
      </footer>
    </div>
  )
}