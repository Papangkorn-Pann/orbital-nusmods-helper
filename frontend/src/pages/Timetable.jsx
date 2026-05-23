import { useState, useEffect } from 'react'
import { getUserId } from '../App.jsx'
import { getTimetable, updateSlot, removeModule } from '../api.js'
import ModulePanel from '../components/timetable/ModulePanel.jsx'
import TimetableGrid from '../components/timetable/TimetableGrid.jsx'

const PALETTE = [
  '#3b82f6','#10b981','#f59e0b','#8b5cf6',
  '#ef4444','#06b6d4','#f97316','#6366f1',
  '#14b8a6','#ec4899','#84cc16','#a78bfa',
]

export default function Timetable() {
  const userId = getUserId()
  const [sem, setSem] = useState(2)   // default to Sem 2 (we're in May 2026)
  const [selections, setSelections]     = useState({})  // { code: { lessonType: classNo } }
  const [renderedSlots, setRenderedSlots] = useState([])
  const [saving, setSaving] = useState(false)

  // Assign a stable color to each module code
  const moduleCodes = Object.keys(selections)
  const moduleColors = Object.fromEntries(
    moduleCodes.map((c, i) => [c, PALETTE[i % PALETTE.length]])
  )

  // Load saved timetable on mount / sem change
  useEffect(() => {
    getTimetable(userId, sem).then(data => {
      const sel = {}
      for (const s of data.selections) {
        sel[s.module_code] = sel[s.module_code] || {}
        sel[s.module_code][s.lesson_type] = s.class_no
      }
      setSelections(sel)
      setRenderedSlots(data.rendered_slots || [])
    }).catch(() => {})
  }, [sem])

  async function handleSlotChange(code, lessonType, classNo) {
    // Optimistic update
    setSelections(prev => ({
      ...prev,
      [code]: { ...(prev[code] || {}), [lessonType]: classNo },
    }))
    setSaving(true)
    try {
      await updateSlot(userId, { module_code: code, lesson_type: lessonType, class_no: classNo, sem })
      // Refresh rendered slots from backend
      const data = await getTimetable(userId, sem)
      setRenderedSlots(data.rendered_slots || [])
    } finally {
      setSaving(false)
    }
  }

  async function handleRemoveModule(code) {
    setSelections(prev => {
      const next = { ...prev }
      delete next[code]
      return next
    })
    await removeModule(userId, code, sem)
    const data = await getTimetable(userId, sem)
    setRenderedSlots(data.rendered_slots || [])
  }

  return (
    <div className="page">
      <div style={styles.topBar}>
        <h1 className="page-title" style={{ marginBottom: 0 }}>Timetable Builder</h1>
        <div style={styles.semSwitch}>
          {[1, 2].map(s => (
            <button
              key={s}
              onClick={() => setSem(s)}
              className={sem === s ? 'btn-primary' : 'btn-ghost'}
              style={{ padding: '6px 18px' }}
            >
              Sem {s}
            </button>
          ))}
        </div>
        {saving && <span style={styles.saving}>Saving…</span>}
      </div>

      <div style={styles.layout}>
        {/* Left panel */}
        <div style={styles.panelCol}>
          <ModulePanel
            sem={sem}
            selections={selections}
            onSlotChange={handleSlotChange}
            onRemoveModule={handleRemoveModule}
            moduleColors={moduleColors}
          />
        </div>

        {/* Timetable grid */}
        <div style={styles.gridCol}>
          <TimetableGrid
            renderedSlots={renderedSlots}
            moduleColors={moduleColors}
          />
          {moduleCodes.length === 0 && (
            <p style={styles.hint}>Add modules from the left panel to see them here.</p>
          )}
        </div>
      </div>
    </div>
  )
}

const styles = {
  topBar: {
    display: 'flex',
    alignItems: 'center',
    gap: 16,
    marginBottom: 20,
    flexWrap: 'wrap',
  },
  semSwitch: { display: 'flex', gap: 6 },
  saving: { color: '#94a3b8', fontSize: 13 },
  layout: {
    display: 'grid',
    gridTemplateColumns: '300px 1fr',
    gap: 20,
    alignItems: 'start',
  },
  panelCol: {
    position: 'sticky',
    top: 72,
    maxHeight: 'calc(100vh - 90px)',
    overflowY: 'auto',
  },
  gridCol: {},
  hint: { color: '#94a3b8', textAlign: 'center', marginTop: 40, fontSize: 14 },
}
