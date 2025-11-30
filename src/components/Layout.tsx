import { Outlet, useNavigate } from 'react-router-dom'
import { useAuthStore, useNotificationStore } from '@/store'
import { Bell, LogOut, Menu } from 'lucide-react'
import { useState } from 'react'
import { auth } from '@/api'

export default function Layout() {
  const { user } = useAuthStore()
  const { notifications } = useNotificationStore()
  const navigate = useNavigate()
  const [showMenu, setShowMenu] = useState(false)

  const handleLogout = async () => {
    await auth.logout()
    navigate('/login')
  }

  const unreadCount = notifications.filter((n) => !n.read).length

  return (
    <div className="min-h-screen bg-black">
      {/* Header */}
      <header className="bg-[#f89643] shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div 
              className="flex items-center gap-3 cursor-pointer hover:opacity-80 transition-opacity" 
              onClick={() => navigate('/')}
              title="Go to Dashboard"
            >
              <img src="/static/Docs-Hub.png" alt="DocsHub Logo" className="h-10 w-10" />
              <h1 className="text-2xl font-bold text-black">DocsHub</h1>
            </div>

            <div className="flex items-center gap-4">
              {/* User Info */}
              {user && (
                <div className="text-right mr-2">
                  <div className="font-bold text-black text-sm">{user.username}</div>
                  <div className="text-xs text-black/70">{user.email}</div>
                </div>
              )}
              
              {/* Notifications */}
              <button className="relative p-2 text-black hover:text-black/80">
                <Bell size={20} />
                {unreadCount > 0 && (
                  <span className="absolute top-0 right-0 bg-red-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                    {unreadCount}
                  </span>
                )}
              </button>

              {/* User Menu */}
              <div className="relative">
                <button
                  onClick={() => setShowMenu(!showMenu)}
                  className="p-2 text-black hover:text-black/80"
                >
                  <Menu size={20} />
                </button>
                {showMenu && (
                  <div className="absolute right-0 mt-2 w-48 bg-[#f89643] rounded-lg shadow-lg py-2 z-50 border border-black/20">
                    <div className="px-4 py-2 border-b border-black/20 text-sm text-black">
                      {user?.email}
                    </div>
                    <button
                      onClick={handleLogout}
                      className="w-full text-left px-4 py-2 text-black hover:bg-black/10 flex items-center gap-2"
                    >
                      <LogOut size={16} />
                      Logout
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>
    </div>
  )
}
