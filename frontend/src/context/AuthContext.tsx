
// Auth context for OIDC authentication
import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import { api, setAuthToken } from '../api/client'

interface User {
  id: string
  email: string | null
  username: string | null
  full_name: string | null
  roles: string[]
  is_active: boolean
  is_superuser: boolean
}

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (redirectUri?: string) => Promise<void>
  logout: (redirectUri?: string) => Promise<void>
  refreshUser: () => Promise<void>
  hasRole: (role: string) => boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    try {
      const userData = await api.getMe()
      setUser(userData)
      setAuthToken('')
    } catch {
      setUser(null)
      setAuthToken(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    refreshUser()
  }, [refreshUser])

  const login = useCallback(async (redirectUri = window.location.origin) => {
    sessionStorage.setItem('auth_redirect', redirectUri)
    const { auth_url, state, nonce } = await api.getAuthUrl(redirectUri)
    sessionStorage.setItem('oidc_state', state)
    sessionStorage.setItem('oidc_nonce', nonce)
    window.location.href = auth_url
  }, [])

  const logout = useCallback(async (redirectUri = window.location.origin) => {
    try {
      const { logout_url } = await api.logout(redirectUri)
      setUser(null)
      setAuthToken(null)
      window.location.href = logout_url
    } catch {
      setUser(null)
      setAuthToken(null)
      window.location.href = redirectUri
    }
  }, [])

  const hasRole = useCallback((role: string) => {
    return user?.roles.includes(role) || user?.roles.includes('admin') || false
  }, [user])

  return (
    <AuthContext.Provider value={{
      user,
      isLoading,
      isAuthenticated: !!user,
      login,
      logout,
      refreshUser,
      hasRole,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
