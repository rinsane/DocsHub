import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Trash2, Share2, FileText, Table } from 'lucide-react'
import { documents, spreadsheets } from '@/api'

interface Doc {
  id: number
  title: string
  created_at: string
  owner: { username: string }
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [docs, setDocs] = useState<Doc[]>([])
  const [sheets, setSheets] = useState<Doc[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadData = async () => {
      try {
        const [docsRes, sheetsRes] = await Promise.all([
          documents.list(),
          spreadsheets.list(),
        ])
        setDocs(docsRes.data)
        setSheets(sheetsRes.data)
      } catch (error) {
        console.error('Failed to load files:', error)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  const handleCreateDoc = async () => {
    try {
      const res = await documents.create('Untitled Document')
      navigate(`/documents/${res.data.id}`)
    } catch (error) {
      console.error('Failed to create document:', error)
    }
  }

  const handleCreateSheet = async () => {
    try {
      const res = await spreadsheets.create('Untitled Spreadsheet')
      navigate(`/spreadsheets/${res.data.id}`)
    } catch (error) {
      console.error('Failed to create spreadsheet:', error)
    }
  }

  const handleDelete = async (id: number, type: 'document' | 'spreadsheet') => {
    if (confirm('Are you sure you want to delete this?')) {
      try {
        if (type === 'document') {
          await documents.delete(id)
          setDocs(docs.filter((d) => d.id !== id))
        } else {
          await spreadsheets.delete(id)
          setSheets(sheets.filter((s) => s.id !== id))
        }
      } catch (error) {
        console.error('Failed to delete:', error)
      }
    }
  }

  if (loading) {
    return <div className="text-center py-8">Loading...</div>
  }

  return (
    <div className="space-y-8">
      {/* Documents */}
      <section>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <FileText size={28} />
            Documents
          </h2>
          <button onClick={handleCreateDoc} className="btn btn-primary flex items-center gap-2">
            <Plus size={18} />
            New Document
          </button>
        </div>

        {docs.length === 0 ? (
          <div className="text-center py-12 bg-gray-100 rounded-lg">
            <p className="text-gray-600">No documents yet. Create one to get started!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {docs.map((doc) => (
              <div key={doc.id} className="card p-4 hover:shadow-lg transition-shadow cursor-pointer">
                <h3 className="font-semibold text-lg mb-2">{doc.title}</h3>
                <p className="text-sm text-gray-600 mb-4">
                  by {doc.owner.username}
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => navigate(`/documents/${doc.id}`)}
                    className="flex-1 btn btn-primary text-sm"
                  >
                    Open
                  </button>
                  <button className="btn btn-secondary p-2">
                    <Share2 size={18} />
                  </button>
                  <button
                    onClick={() => handleDelete(doc.id, 'document')}
                    className="btn btn-danger p-2"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Spreadsheets */}
      <section>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Table size={28} />
            Spreadsheets
          </h2>
          <button onClick={handleCreateSheet} className="btn btn-primary flex items-center gap-2">
            <Plus size={18} />
            New Spreadsheet
          </button>
        </div>

        {sheets.length === 0 ? (
          <div className="text-center py-12 bg-gray-100 rounded-lg">
            <p className="text-gray-600">No spreadsheets yet. Create one to get started!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sheets.map((sheet) => (
              <div key={sheet.id} className="card p-4 hover:shadow-lg transition-shadow">
                <h3 className="font-semibold text-lg mb-2">{sheet.title}</h3>
                <p className="text-sm text-gray-600 mb-4">
                  by {sheet.owner.username}
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => navigate(`/spreadsheets/${sheet.id}`)}
                    className="flex-1 btn btn-primary text-sm"
                  >
                    Open
                  </button>
                  <button className="btn btn-secondary p-2">
                    <Share2 size={18} />
                  </button>
                  <button
                    onClick={() => handleDelete(sheet.id, 'spreadsheet')}
                    className="btn btn-danger p-2"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
