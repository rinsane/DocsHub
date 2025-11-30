import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store'
import { useEffect } from 'react'
import { auth } from './api'

// Pages
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import DocumentEditor from './pages/DocumentEditor'
import SpreadsheetEditor from './pages/SpreadsheetEditor'
import Layout from './components/Layout'

function App() {
  const { user, setUser } = useAuthStore()

  useEffect(() => {
    const checkAuth = async () => {
      // Don't clear user immediately - wait for auth check
      try {
        const res = await auth.getProfile()
        if (res.data) {
          setUser(res.data)
        } else {
          setUser(null)
        }
      } catch (error: any) {
        // Only clear user if it's a 401 (unauthorized), not network errors or 500s
        const status = error.response?.status
        if (status === 401) {
          // Only clear if we don't have a user, or if we're sure it's an auth error
          setUser(null)
        } else if (!status) {
          // Network error - don't clear user, might be temporary
          console.warn('Network error checking auth, keeping current user state')
        } else if (status >= 500) {
          // Server error - don't clear user
          console.warn('Server error checking auth, keeping current user state')
        }
        // For other errors, keep the current user state
      }
    }
    checkAuth()
  }, [setUser])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/*"
          element={user ? <Layout /> : <Navigate to="/login" />}
        >
          <Route index element={<Dashboard />} />
          <Route path="documents/:id" element={<DocumentEditor />} />
          <Route path="spreadsheets/:id" element={<SpreadsheetEditor />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
