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
      try {
        const res = await auth.getProfile()
        setUser(res.data)
      } catch {
        setUser(null)
      }
    }
    checkAuth()
  }, [])

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
