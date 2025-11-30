import { useEffect, useState, useRef } from 'react'
import { useParams } from 'react-router-dom'
import ReactQuill from 'react-quill'
import { documents } from '@/api'
import WebSocketManager from '@/services/websocket'
import { useAuthStore } from '@/store'
import { Save, Share2, MoreVertical } from 'lucide-react'
import 'react-quill/dist/quill.snow.css'

export default function DocumentEditor() {
  const { id } = useParams()
  const { user } = useAuthStore()
  const [content, setContent] = useState('')
  const [title, setTitle] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [activeUsers, setActiveUsers] = useState<string[]>([])
  const [isLocalEdit, setIsLocalEdit] = useState(false)
  const wsRef = useRef<WebSocketManager | null>(null)
  const saveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const contentRef = useRef<string>('')

  useEffect(() => {
    const loadDocument = async () => {
      try {
        const res = await documents.get(Number(id))
        setTitle(res.data.title)
        setContent(res.data.content)
        contentRef.current = res.data.content
      } catch (error) {
        console.error('Failed to load document:', error)
      } finally {
        setLoading(false)
      }
    }

    loadDocument()

    // Setup WebSocket
    if (id) {
      wsRef.current = new WebSocketManager('document', Number(id))
      wsRef.current.connect()

      wsRef.current.on('connected', () => {
        console.log('WebSocket connected for document', id)
        // Add current user to active users list
        if (user?.username) {
          setActiveUsers([user.username])
        }
      })

      wsRef.current.on('content_change', (data) => {
        // Only update if we're not currently editing locally and it's from another user
        // This prevents overwriting user's typing
        if (!isLocalEdit && data.user_id !== user?.id && data.content !== contentRef.current) {
          setContent(data.content)
          contentRef.current = data.content
        }
      })

      wsRef.current.on('active_users', (data) => {
        if (data.users && Array.isArray(data.users)) {
          const usernames = data.users.map((u: any) => u.username)
          setActiveUsers(usernames)
        }
      })

      wsRef.current.on('user_joined', (data) => {
        if (data.username) {
          setActiveUsers((prev) => {
            if (!prev.includes(data.username)) {
              return [...prev, data.username]
            }
            return prev
          })
        }
      })

      wsRef.current.on('user_left', (data) => {
        if (data.username) {
          setActiveUsers((prev) => prev.filter((u) => u !== data.username))
        }
      })

      wsRef.current.on('error', (error) => {
        console.error('WebSocket error:', error)
      })
    }

    return () => {
      wsRef.current?.disconnect()
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current)
      }
    }
  }, [id, user])

  const handleSave = async () => {
    setSaving(true)
    try {
      await documents.update(Number(id), { content, title })
      wsRef.current?.send({ type: 'content_update', content, title })
    } catch (error) {
      console.error('Failed to save:', error)
    } finally {
      setSaving(false)
    }
  }

  const handleChange = (newContent: string) => {
    setIsLocalEdit(true)
    setContent(newContent)
    contentRef.current = newContent

    // Send real-time update via WebSocket
    if (wsRef.current && wsRef.current.ws?.readyState === WebSocket.OPEN) {
      wsRef.current.send({ 
        type: 'content_update', 
        content: newContent,
        title: title
      })
    }

    // Reset local edit flag after a short delay
    setTimeout(() => setIsLocalEdit(false), 100)

    // Debounced save
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current)
    }
    saveTimeoutRef.current = setTimeout(handleSave, 1500)
  }

  if (loading) {
    return <div className="text-center py-8">Loading document...</div>
  }

  const handleShare = async () => {
    const email = prompt('Enter email address to share with:')
    if (!email) return
    
    const role = prompt('Enter role (viewer/editor/commenter):', 'viewer') || 'viewer'
    
    try {
      await documents.share(Number(id), email, role)
      alert('Document shared successfully!')
    } catch (error: any) {
      alert(error.response?.data?.error || 'Failed to share document')
    }
  }

  return (
    <div className="h-screen flex flex-col bg-black">
      {/* Header */}
      <div className="border-b-2 border-orange-500 bg-[#f89643] p-4 flex justify-between items-center">
        <div className="flex-1">
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="text-2xl font-bold outline-none bg-transparent text-black placeholder-black/50"
            placeholder="Document Title"
          />
          <p className="text-sm text-black/80 mt-1">
            Active: {activeUsers.length > 0 ? activeUsers.join(', ') : (user?.username || 'You')}
          </p>
        </div>

        <div className="flex gap-2 items-center">
          <button
            onClick={handleSave}
            disabled={saving}
            className="btn bg-black text-white hover:bg-gray-800 flex items-center gap-2"
          >
            <Save size={18} />
            {saving ? 'Saving...' : 'Save'}
          </button>
          <button 
            onClick={handleShare}
            className="btn bg-black text-white hover:bg-gray-800 p-2"
            title="Share document"
          >
            <Share2 size={18} />
          </button>
          <button className="btn bg-black text-white hover:bg-gray-800 p-2">
            <MoreVertical size={18} />
          </button>
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1 overflow-hidden bg-white">
        <style>{`
          .ql-editor {
            color: black !important;
          }
          .ql-container {
            color: black !important;
          }
        `}</style>
        <ReactQuill
          value={content}
          onChange={handleChange}
          theme="snow"
          modules={{
            toolbar: [
              [{ header: [1, 2, 3, false] }],
              ['bold', 'italic', 'underline', 'strike'],
              ['blockquote', 'code-block'],
              [{ list: 'ordered' }, { list: 'bullet' }],
              ['link', 'image'],
              ['clean'],
            ],
          }}
          style={{ height: '100%' }}
        />
      </div>
    </div>
  )
}
