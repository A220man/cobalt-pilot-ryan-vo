
// OIDC callback page - handles redirect from Keycloak
import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api, setAuthToken } from '../api/client'
import { useAuth } from '../context/AuthContext'

export function AuthCallbackPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { refreshUser } = useAuth()

  const code = searchParams.get('code')
  const state = searchParams.get('state')
  const error = searchParams.get('error')
  const errorDescription = searchParams.get('error_description')
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    async function handleCallback() {
      if (error) {
        setErrorMessage(errorDescription || error || 'Authentication failed')
        setIsLoading(false)
        return
      }

      if (!code || !state) {
        setErrorMessage('Invalid callback: missing code or state')
        setIsLoading(false)
        return
      }

      // Retrieve stored nonce from sessionStorage
      const storedState = sessionStorage.getItem('oidc_state')
      const storedNonce = sessionStorage.getItem('oidc_nonce')

      if (storedState !== state) {
        setErrorMessage('Invalid state parameter')
        setIsLoading(false)
        return
      }

      try {
        const tokens = await api.exchangeCode(code, state, storedNonce || '')
        setAuthToken(tokens.access_token)
        await refreshUser()

        // Redirect to stored redirect URI or home
        const redirectUri = sessionStorage.getItem('auth_redirect') || '/plugins'
        sessionStorage.removeItem('auth_redirect')
        sessionStorage.removeItem('oidc_state')
        sessionStorage.removeItem('oidc_nonce')
        navigate(redirectUri, { replace: true })
      } catch (err) {
        setErrorMessage(err instanceof Error ? err.message : 'Authentication failed')
        setIsLoading(false)
      }
    }

    handleCallback()
  }, [code, state, error, errorDescription, navigate, refreshUser])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-emerald-600 border-t-transparent mx-auto mb-4"></div>
          <p className="text-slate-600 dark:text-slate-400">Completing sign in...</p>
        </div>
      </div>
    )
  }

  if (errorMessage) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="text-center p-8 max-w-md mx-4">
          <svg className="w-16 h-16 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">Sign In Failed</h1>
          <p className="text-slate-600 dark:text-slate-400 mb-6">{errorMessage}</p>
          <button
            onClick={() => navigate('/plugins', { replace: true })}
            className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
          >
            Go to Plugins
          </button>
        </div>
      </div>
    )
  }

  return null
}
