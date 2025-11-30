import { useEffect, useState, useRef } from 'react'
import { useParams } from 'react-router-dom'
import ReactQuill from 'react-quill'
import { documents } from '@/api'
import { useAuthStore } from '@/store'
import { Save, Share2, MoreVertical, Download } from 'lucide-react'
import 'react-quill/dist/quill.snow.css'
import WebSocketManager from '@/services/websocket'

export default function DocumentEditor() {
  const { id } = useParams()
  const { user } = useAuthStore()
  const [content, setContent] = useState('')
  const [title, setTitle] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [activeUsers, setActiveUsers] = useState<string[]>([])
  const [userRole, setUserRole] = useState<string>('viewer')
  const [showMenu, setShowMenu] = useState(false)
  
  const wsRef = useRef<WebSocketManager | null>(null)
  const quillRef = useRef<ReactQuill | null>(null)
  const saveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const lastContentRef = useRef<string>('')
  const isUpdatingFromRemote = useRef(false)

  useEffect(() => {
    const loadDocument = async () => {
      try {
        const res = await documents.get(Number(id))
        const docData = res.data
        
        setTitle(docData.title || 'Untitled Document')
        const initialContent = docData.content || '<p><br></p>'
        setContent(initialContent)
        lastContentRef.current = initialContent
        setUserRole(docData.role || 'viewer')
        
        // Set initial content in Quill after it's loaded
        setTimeout(() => {
          if (quillRef.current && initialContent) {
            const quill = quillRef.current.getEditor()
            if (quill.root.innerHTML === '<p><br></p>' || quill.root.innerHTML === '') {
              quill.clipboard.dangerouslyPasteHTML(0, initialContent, 'silent')
            }
          }
        }, 50)
        
        setLoading(false)
      } catch (error) {
        console.error('Failed to load document:', error)
        setLoading(false)
      }
    }

    loadDocument()

    // Setup WebSocket
    if (id) {
      wsRef.current = new WebSocketManager('document', Number(id))
      wsRef.current.connect()

      // Handle content updates from other users - IMMEDIATE sync
      wsRef.current.on('content_update', (data: any) => {
        if (quillRef.current && data.content && data.content !== lastContentRef.current) {
          const quill = quillRef.current.getEditor()
          const currentContent = quill.root.innerHTML
          
          // Only update if content is different to avoid loops
          if (data.content !== currentContent) {
            // Set flag BEFORE making any changes
            isUpdatingFromRemote.current = true
            lastContentRef.current = data.content
            
            // Preserve cursor position
            const selection = quill.getSelection()
            
            // Disable the editor temporarily to prevent text-change events
            const wasReadOnly = (quill as any).container.firstChild.contentEditable === 'false'
            quill.disable()
            
            // REPLACE content entirely using setContents with clipboard conversion
            const delta = quill.clipboard.convert(data.content)
            quill.setContents(delta, 'silent')
            
            // Re-enable if it wasn't read-only
            if (!wasReadOnly) {
              quill.enable()
            }
            
            // Restore cursor position
            if (selection && selection.index >= 0) {
              try {
                const newLength = quill.getLength()
                const safeIndex = Math.min(selection.index, newLength - 1)
                quill.setSelection(safeIndex, 0, 'silent')
              } catch (e) {
                // Ignore invalid selection
              }
            }
            
            // Keep flag set for a bit longer to prevent echo
            setTimeout(() => {
              isUpdatingFromRemote.current = false
            }, 50)
          }
        }
      })

      // Handle title updates
      wsRef.current.on('title_update', (data: any) => {
        if (data.title !== title) {
          setTitle(data.title)
        }
      })

      // Handle user joined/left
      wsRef.current.on('user_joined', (data: any) => {
        setActiveUsers((prev) => {
          if (!prev.includes(data.username)) {
            return [...prev, data.username]
          }
          return prev
        })
      })

      wsRef.current.on('user_left', (data: any) => {
        setActiveUsers((prev) => prev.filter((u) => u !== data.username))
      })

      // Handle active users list
      wsRef.current.on('active_users', (data: any) => {
        if (data.users && Array.isArray(data.users)) {
          setActiveUsers(data.users)
        }
      })
    }

    // Setup Quill text-change listener for immediate WebSocket updates
    let textChangeHandler: ((delta: any, oldDelta: any, source: string) => void) | null = null
    
    const setupQuillListener = () => {
      if (quillRef.current) {
        const quill = quillRef.current.getEditor()
        
        // Listen to text-change event for IMMEDIATE updates
        textChangeHandler = (_delta: any, _oldDelta: any, source: string) => {
          // ONLY send if it's a real user action, not programmatic or remote
          if (source === 'user' && !isUpdatingFromRemote.current) {
            const html = quill.root.innerHTML
            
            // Only send if content actually changed
            if (html !== lastContentRef.current) {
              lastContentRef.current = html
              
              // Send IMMEDIATELY via WebSocket - no delays, no flags
              if (wsRef.current && (userRole === 'owner' || userRole === 'editor')) {
                wsRef.current.send({
                  type: 'content_update',
                  content: html,
                  document_id: Number(id)
                })
              }
              
              // Debounce database save (separate from real-time sync)
              if (saveTimeoutRef.current) {
                clearTimeout(saveTimeoutRef.current)
              }
              saveTimeoutRef.current = setTimeout(async () => {
                try {
                  await documents.update(Number(id), {
                    content: html,
                    title: title
                  })
                  console.log('Auto-saved to database')
                } catch (error) {
                  console.error('Auto-save failed:', error)
                }
              }, 2000)
            }
          }
        }
        
        quill.on('text-change', textChangeHandler)
      }
    }

    // Setup listener after Quill is ready - check multiple times to ensure it's set up
    const timer = setTimeout(setupQuillListener, 200)
    const timer2 = setTimeout(setupQuillListener, 500)

    return () => {
      clearTimeout(timer)
      clearTimeout(timer2)
      wsRef.current?.disconnect()
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current)
      }
      // Remove Quill listeners
      if (quillRef.current && textChangeHandler) {
        try {
          const quill = quillRef.current.getEditor()
          quill.off('text-change', textChangeHandler)
        } catch (e) {
          // Ignore if Quill is already destroyed
        }
      }
    }
  }, [id, title, userRole])

  // Handle content changes from Quill
  const handleContentChange = (value: string) => {
    // Update state to keep React in sync, but this won't cause re-render issues
    // because we're using defaultValue
    if (!isUpdatingFromRemote.current) {
      setContent(value)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await documents.update(Number(id), {
        content: content,
        title: title
      })
      // Document saved successfully (no alert popup)
      console.log('Document saved successfully!')
    } catch (error: any) {
      console.error('Failed to save:', error)
      alert('Failed to save: ' + (error.response?.data?.error || error.message))
    } finally {
      setSaving(false)
    }
  }

  const handleTitleChange = (newTitle: string) => {
    if (userRole === 'owner' || userRole === 'editor') {
      setTitle(newTitle)
      
      // Send title update via WebSocket
      if (wsRef.current) {
        wsRef.current.send({
          type: 'title_update',
          title: newTitle,
          document_id: Number(id)
        })
      }
      
      // Save title immediately
      documents.update(Number(id), {
        content: content,
        title: newTitle
      }).catch(err => {
        console.error('Failed to save title:', err)
      })
    }
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

  const handleDownloadTxt = () => {
    try {
      let textContent = ''
      
      if (quillRef.current) {
        const quill = quillRef.current.getEditor()
        textContent = quill.getText() // Get plain text without HTML
      } else {
        // Fallback: use content state if Quill not available
        const tempDiv = document.createElement('div')
        tempDiv.innerHTML = content
        textContent = tempDiv.textContent || tempDiv.innerText || ''
      }
      
      if (!textContent.trim()) {
        alert('Document is empty')
        return
      }
      
      // Create blob and download
      const blob = new Blob([textContent], { type: 'text/plain;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      const safeTitle = (title || 'document').replace(/[^a-z0-9\s-]/gi, '_').replace(/\s+/g, '_')
      a.download = `${safeTitle}.txt`
      a.style.display = 'none'
      document.body.appendChild(a)
      a.click()
      
      // Clean up
      setTimeout(() => {
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
      }, 100)
      
      console.log('Download initiated successfully')
    } catch (error) {
      console.error('Download error:', error)
      alert('Failed to download document: ' + (error instanceof Error ? error.message : 'Unknown error'))
    }
  }

  const canEdit = userRole === 'owner' || userRole === 'editor'

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-black">
        <div className="text-center text-white">
          <div className="text-xl mb-2">Loading document...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col bg-black">
      {/* Header */}
      <div className="border-b-2 border-orange-500 bg-[#f89643] p-4 flex justify-between items-center">
        <div className="flex-1">
          <input
            type="text"
            value={title}
            onChange={(e) => handleTitleChange(e.target.value)}
            disabled={!canEdit}
            className="text-2xl font-bold outline-none bg-transparent text-black placeholder-black/50 disabled:opacity-50"
            placeholder="Document Title"
          />
          <p className="text-sm text-black/80 mt-1">
            Active: {activeUsers.length > 0 ? activeUsers.join(', ') : user?.username || 'You'}
            {!canEdit && <span className="ml-2">(Read-only)</span>}
          </p>
        </div>

        <div className="flex gap-2 items-center">
          <button
            onClick={handleSave}
            disabled={saving || !canEdit}
            className="btn bg-black text-white hover:bg-gray-800 flex items-center gap-2 disabled:opacity-50"
          >
            <Save size={18} />
            {saving ? 'Saving...' : 'Save'}
          </button>
          {canEdit && (
            <button 
              onClick={handleShare}
              className="btn bg-black text-white hover:bg-gray-800 p-2"
              title="Share document"
            >
              <Share2 size={18} />
            </button>
          )}
          <div className="relative" onClick={(e) => e.stopPropagation()}>
            <button 
              className="btn bg-black text-white hover:bg-gray-800 p-2" 
              title="More options"
              onClick={(e) => {
                e.stopPropagation()
                setShowMenu(!showMenu)
              }}
            >
              <MoreVertical size={18} />
            </button>
            {/* Dropdown menu */}
            {showMenu && (
              <div 
                className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded shadow-lg z-50"
                onClick={(e) => e.stopPropagation()}
              >
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                    handleDownloadTxt()
                    setShowMenu(false)
                  }}
                  className="w-full text-left px-4 py-2 text-black hover:bg-gray-100 flex items-center gap-2 transition-colors cursor-pointer"
                >
                  <Download size={16} />
                  Download as .txt
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1 overflow-hidden bg-white">
        <style>{`
          .ql-container {
            height: 100% !important;
            display: flex !important;
            flex-direction: column !important;
          }
          .ql-toolbar {
            border: none !important;
            border-bottom: 1px solid #ccc !important;
            background: white !important;
          }
          .ql-editor {
            flex: 1 !important;
            color: black !important;
            overflow-y: auto !important;
            min-height: 200px !important;
          }
          .ql-container .ql-editor {
            min-height: 100% !important;
          }
        `}</style>
        <ReactQuill
          ref={quillRef}
          defaultValue={content}
          onChange={handleContentChange}
          readOnly={!canEdit}
          theme="snow"
          placeholder={canEdit ? "Start typing..." : "Read-only"}
          modules={{
            toolbar: canEdit ? [
              [{ header: [1, 2, 3, false] }],
              ['bold', 'italic', 'underline', 'strike'],
              ['blockquote', 'code-block'],
              [{ list: 'ordered' }, { list: 'bullet' }],
              ['link', 'image'],
              ['clean'],
            ] : false,
          }}
          style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
          formats={[
            'header', 'bold', 'italic', 'underline', 'strike',
            'blockquote', 'code-block', 'list', 'bullet',
            'link', 'image'
          ]}
          key={`quill-${id}`}
        />
      </div>
    </div>
  )
}
