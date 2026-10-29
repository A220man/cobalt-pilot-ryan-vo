// Main App component
import { Routes, Route, Navigate } from 'react-router-dom'
import { PluginListPage } from './pages/PluginListPage'
import { PluginDetailPage } from './pages/PluginDetailPage'
import { AuthCallbackPage } from './pages/AuthCallbackPage'
import { Layout } from './components/Layout'
import { AuthProvider } from './context/AuthContext'

function App() {
  return (
    <AuthProvider>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/plugins" replace />} />
          <Route path="/plugins" element={<PluginListPage />} />
          <Route path="/plugins/:slug" element={<PluginDetailPage />} />
          <Route path="/auth/callback" element={<AuthCallbackPage />} />
          <Route path="*" element={<Navigate to="/plugins" replace />} />
        </Routes>
      </Layout>
    </AuthProvider>
  )
}

export default App