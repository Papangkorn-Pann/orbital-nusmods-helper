import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getSharedTimetable } from '../api.js'
import TimetableGrid from '../components/timetable/TimetableGrid.jsx'

const PALETTE = [
  '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6',
  '#ef4444', '#06b6d4', '#f97316', '#6366f1',
  '#14b8a6', '#ec4899', '#84cc16', '#a78bfa',
]

export default function SharedTimetable() {
  const { token }     = useParams()
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState('')

  useEffect(() => {
    getSharedTimetable(token)
      .then(setData)
      .catch(() => setError('Share link not found or has expired.'))
      .finally(() => setLoading(false))
  }, [token])

  if (loading) {
    return (
      <div className="page">
        <p style={{ color: '#64748b' }}>Loading shared timetable…</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page">
        <p style={{ color: '#ef4444', fontWeight: 600 }}>{error}</p>
        <Link to="/timetable">
          <button className="btn-primary" style={{ marginTop: 16 }}>
            Build my own timetable
          </button>
        </Link>
      </div>
    )
  }

  if (!data) return null

  const moduleCodes  = data.module_codes || []
  const moduleColors = Object.fromEntries(
    moduleCodes.map((c, i) => [c, PALETTE[i % PALETTE.length]])
  )

  return (
    <div className="page">
      <div style={s.topBar}>
        <h1 className="page-title" style={{ marginBottom: 0 }}>Shared Timetable</h1>
        <span style={s.semBadge}>Sem {data.sem}</span>
        <span style={s.readOnly}>Read-only</span>
        {data.created_at && (
          <span style={s.meta}>
            Shared on {data.created_at.slice(0, 10)}
          </span>
        )}
      </div>

      {/* Module badges */}
      <div style={s.modules}>
        {moduleCodes.map(mc => (
          <span
            key={mc}
            style={{
              ...s.modTag,
              background: moduleColors[mc] + '20',
              color: moduleColors[mc],
            }}
          >
            {mc}
          </span>
        ))}
      </div>

      <TimetableGrid
        renderedSlots={data.rendered_slots || []}
        moduleColors={moduleColors}
      />

      <div style={{ marginTop: 20, textAlign: 'right' }}>
        <Link to="/timetable">
          <button className="btn-primary">Build my own timetable →</button>
        </Link>
      </div>
    </div>
  )
}

const s = {
  topBar: {
    display: 'flex', alignItems: 'center', gap: 12,
    marginBottom: 16, flexWrap: 'wrap',
  },
  semBadge: {
    background: '#eff6ff', color: '#2563eb',
    fontWeight: 700, fontSize: 13,
    padding: '4px 12px', borderRadius: 20,
  },
  readOnly: {
    background: '#f1f5f9', color: '#64748b',
    fontSize: 12, padding: '4px 10px', borderRadius: 20,
    border: '1px solid #e2e8f0',
  },
  meta: { color: '#94a3b8', fontSize: 12 },
  modules: { display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 20 },
  modTag: {
    padding: '4px 14px', borderRadius: 20,
    fontWeight: 700, fontSize: 13,
  },
}
