// Main App component
import { Routes, Route } from 'react-router-dom'
import { PluginListPage } from './pages/PluginListPage'
import { PluginDetailPage } from './pages/PluginDetailPage'
import { Layout } from './components/Layout'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/plugins" replace />} />
        <Route path="/plugins" element={<PluginListPage />} />
        <Route path="/plugins/:slug" element={<PluginDetailPage />} />
        <Route path="*" element={<Navigate to="/plugins" replace />} />
      </Routes>
    </Layout>
  )
}

import { Navigate } from 'react-router-dom'

export default App