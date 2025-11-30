import { useEffect, useState, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { HotTable } from '@handsontable/react'
import { registerAllModules } from 'handsontable/registry'
import { spreadsheets } from '@/api'
import WebSocketManager from '@/services/websocket'
import { Save, Share2, MoreVertical } from 'lucide-react'
import 'handsontable/dist/handsontable.full.min.css'

registerAllModules()

export default function SpreadsheetEditor() {
  const { id } = useParams()
  const [data, setData] = useState<any[][]>([])
  const [title, setTitle] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [activeUsers, setActiveUsers] = useState<string[]>([])
  const wsRef = useRef<WebSocketManager | null>(null)
  const saveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    const loadSpreadsheet = async () => {
      try {
        const res = await spreadsheets.get(Number(id))
        setTitle(res.data.title)
        setData(res.data.data?.sheets?.[0]?.data || [])
      } catch (error) {
        console.error('Failed to load spreadsheet:', error)
      } finally {
        setLoading(false)
      }
    }

    loadSpreadsheet()

    // Setup WebSocket
    if (id) {
      wsRef.current = new WebSocketManager('spreadsheet', Number(id))
      wsRef.current.connect()

      wsRef.current.on('cell_change', (msg) => {
        msg.changes?.forEach((change: any) => {
          if (data[change.row]) {
            data[change.row][change.col] = change.value
          }
        })
        setData([...data])
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
      await spreadsheets.update(Number(id), {
        data: { sheets: [{ name: 'Sheet1', data }] },
      })
    } catch (error) {
      console.error('Failed to save:', error)
    } finally {
      setSaving(false)
    }
  }

  const handleChange = () => {
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current)
    }
    saveTimeoutRef.current = setTimeout(handleSave, 1500)
  }

  if (loading) {
    return <div className="text-center py-8">Loading spreadsheet...</div>
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
            placeholder="Spreadsheet Title"
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

      {/* Spreadsheet */}
      <div className="flex-1 overflow-hidden">
        <HotTable
          data={data}
          rowHeaders={true}
          colHeaders={true}
          height="100%"
          afterChange={handleChange}
          contextMenu={true}
          dropdownMenu={true}
          licenseKey="non-commercial-and-evaluation"
        />
      </div>
    </div>
  )
}
