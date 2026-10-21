// SyncButton component
import { useSyncPlugins } from '../hooks/usePlugins'
import { Button } from './Button'
import { useState } from 'react'
import { cn } from '../utils/cn'

export function SyncButton() {
  const { sync, loading, error, result } = useSyncPlugins()
  const [showResult, setShowResult] = useState(false)

  const handleSync = async () => {
    try {
      await sync()
      setShowResult(true)
    } catch {
      // Error handled by hook
    }
  }

  return (
    <div className="space-y-3">
      <Button onClick={handleSync} loading={loading} variant="primary">
        Sync from Reference Repo
      </Button>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {result && showResult && (
        <Alert variant={result.status === 'success' ? 'default' : 'destructive'}>
          <AlertDescription>
            <div className="space-y-1">
              <p className="font-medium capitalize">Sync {result.status}</p>
              <p className="text-sm">Plugins: {result.plugins_synced} | Skills: {result.skills_synced} | Commands: {result.commands_synced} | Connectors: {result.connectors_synced}</p>
              {result.error_message && <p className="text-sm text-red-600 dark:text-red-400">{result.error_message}</p>}
            </div>
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
}

// Simple Alert component
interface AlertProps {
  variant?: 'default' | 'destructive'
  children: React.ReactNode
}

function Alert({ variant = 'default', children }: AlertProps) {
  return (
    <div className={cn(
      'p-3 rounded-lg border text-sm',
      variant === 'destructive'
        ? 'bg-red-50 border-red-200 text-red-800 dark:bg-red-900/20 dark:border-red-800 dark:text-red-200'
        : 'bg-emerald-50 border-emerald-200 text-emerald-800 dark:bg-emerald-900/20 dark:border-emerald-800 dark:text-emerald-200'
    )}>
      {children}
    </div>
  )
}

function AlertDescription({ children }: { children: React.ReactNode }) {
  return <div>{children}</div>
}