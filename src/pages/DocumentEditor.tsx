import { useEffect, useState, useRef } from 'react'
import { useParams } from 'react-router-dom'
import ReactQuill from 'react-quill'
import { documents } from '@/api'
import WebSocketManager from '@/services/websocket'
import { Save, Share2, MoreVertical } from 'lucide-react'
import 'react-quill/dist/quill.snow.css'

export default function DocumentEditor() {
  const { id } = useParams()
  const [content, setContent] = useState('')
  const [title, setTitle] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [activeUsers, setActiveUsers] = useState<string[]>([])
  const wsRef = useRef<WebSocketManager | null>(null)
  const saveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    const loadDocument = async () => {
      try {
        const res = await documents.get(Number(id))
        setTitle(res.data.title)
        setContent(res.data.content)
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

      wsRef.current.on('content_change', (data) => {
        setContent(data.content)
      })

      wsRef.current.on('user_joined', (data) => {
        setActiveUsers((prev) => [...new Set([...prev, data.username])])
      })

      wsRef.current.on('user_left', (data) => {
        setActiveUsers((prev) => prev.filter((u) => u !== data.username))
      })
    }

    return () => {
      wsRef.current?.disconnect()
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current)
    }
    }
  }, [id])

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
    setContent(newContent)

    // Debounced save
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current)
    }
    saveTimeoutRef.current = setTimeout(handleSave, 1500)
  }

  if (loading) {
    return <div className="text-center py-8">Loading document...</div>
  }

  return (
    <div className="h-screen flex flex-col bg-white">
      {/* Header */}
      <div className="border-b bg-gray-50 p-4 flex justify-between items-center">
        <div className="flex-1">
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="text-2xl font-bold outline-none"
            placeholder="Document Title"
          />
          <p className="text-sm text-gray-600 mt-1">
            Active: {activeUsers.join(', ') || 'You'}
          </p>
        </div>

        <div className="flex gap-2 items-center">
          <button
            onClick={handleSave}
            disabled={saving}
            className="btn btn-primary flex items-center gap-2"
          >
            <Save size={18} />
            {saving ? 'Saving...' : 'Save'}
          </button>
          <button className="btn btn-secondary p-2">
            <Share2 size={18} />
          </button>
          <button className="btn btn-secondary p-2">
            <MoreVertical size={18} />
          </button>
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1 overflow-hidden">
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
