import { useState, useEffect, useRef } from 'react'
import { searchModules, getModuleSlots } from '../../api.js'
import SlotChooser from './SlotChooser.jsx'

const PALETTE = [
  '#3b82f6','#10b981','#f59e0b','#8b5cf6',
  '#ef4444','#06b6d4','#f97316','#6366f1',
  '#14b8a6','#ec4899','#84cc16','#a78bfa',
]

export default function ModulePanel({ sem, selections, onSlotChange, onRemoveModule, moduleColors }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [moduleSlots, setModuleSlots] = useState({})  // { code: { by_lesson_type } }
  const debounce = useRef(null)

  // Fetch slot data for all selected modules
  const selectedCodes = Object.keys(selections)
  useEffect(() => {
    selectedCodes.forEach(code => {
      if (!moduleSlots[code]) {
        getModuleSlots(code, sem)
          .then(data => setModuleSlots(prev => ({ ...prev, [code]: data.by_lesson_type })))
          .catch(() => {})
      }
    })
  }, [selectedCodes.join(','), sem])

  // Debounced search
  useEffect(() => {
    clearTimeout(debounce.current)
    if (!query.trim()) { setResults([]); return }
    debounce.current = setTimeout(() => {
      setLoading(true)
      searchModules(query)
        .then(r => { setResults(r); setLoading(false) })
        .catch(() => setLoading(false))
    }, 300)
  }, [query])

  function handleAdd(mod) {
    if (selections[mod.moduleCode]) return  // already added
    setQuery('')
    setResults([])
    // Pick first slot of each lesson type automatically
    getModuleSlots(mod.moduleCode, sem).then(data => {
      setModuleSlots(prev => ({ ...prev, [mod.moduleCode]: data.by_lesson_type }))
      Object.entries(data.by_lesson_type).forEach(([lessonType, slots]) => {
        if (slots.length > 0) {
          onSlotChange(mod.moduleCode, lessonType, slots[0].classNo)
        }
      })
    })
  }

  return (
    <div style={styles.panel}>
      <div style={styles.searchBox}>
        <input
          placeholder="Search module code or title…"
          value={query}
          onChange={e => setQuery(e.target.value)}
          style={styles.input}
        />
        {loading && <span style={styles.spinner}>⏳</span>}
        {results.length > 0 && (
          <div style={styles.dropdown}>
            {results.map(m => (
              <div key={m.moduleCode} style={styles.result} onClick={() => handleAdd(m)}>
                <span style={styles.code}>{m.moduleCode}</span>
                <span style={styles.title}>{m.title}</span>
                {selections[m.moduleCode] && <span style={styles.added}>Added</span>}
              </div>
            ))}
          </div>
        )}
      </div>

      {selectedCodes.length === 0 && (
        <p style={styles.empty}>Search and add modules to build your timetable.</p>
      )}

      {selectedCodes.map(code => {
        const color = moduleColors[code] || '#94a3b8'
        const slots = moduleSlots[code] || {}
        const chosen = selections[code] || {}

        return (
          <div key={code} style={styles.moduleCard}>
            <div style={styles.moduleHeader}>
              <span style={{ ...styles.colorDot, background: color }} />
              <span style={styles.moduleCode}>{code}</span>
              <button
                style={styles.removeBtn}
                onClick={() => onRemoveModule(code)}
                title="Remove module"
              >✕</button>
            </div>

            {Object.entries(slots).map(([lessonType, slotList]) => (
              <SlotChooser
                key={lessonType}
                moduleCode={code}
                lessonType={lessonType}
                slots={slotList}
                selectedClassNo={chosen[lessonType] || slotList[0]?.classNo}
                color={color}
                onSelect={onSlotChange}
              />
            ))}
          </div>
        )
      })}
    </div>
  )
}

const styles = {
  panel: { display: 'flex', flexDirection: 'column', gap: 12, height: '100%', overflowY: 'auto' },
  searchBox: { position: 'relative' },
  input: { width: '100%' },
  spinner: { position: 'absolute', right: 10, top: 9, fontSize: 12 },
  dropdown: {
    position: 'absolute',
    top: '100%',
    left: 0,
    right: 0,
    background: 'white',
    border: '1px solid #e2e8f0',
    borderRadius: 8,
    boxShadow: '0 8px 16px rgba(0,0,0,.1)',
    zIndex: 50,
    maxHeight: 260,
    overflowY: 'auto',
  },
  result: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '10px 12px',
    cursor: 'pointer',
    borderBottom: '1px solid #f1f5f9',
    transition: 'background .1s',
  },
  code:  { fontWeight: 700, fontSize: 13, color: '#2563eb', minWidth: 72 },
  title: { color: '#374151', fontSize: 12, flex: 1 },
  added: { fontSize: 11, color: '#22c55e', fontWeight: 600 },
  empty: { color: '#94a3b8', textAlign: 'center', marginTop: 32, fontSize: 13 },
  moduleCard: {
    background: 'white',
    border: '1px solid #e2e8f0',
    borderRadius: 8,
    padding: 12,
  },
  moduleHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  colorDot: { width: 12, height: 12, borderRadius: '50%', flexShrink: 0 },
  moduleCode: { fontWeight: 700, fontSize: 15, flex: 1 },
  removeBtn: {
    background: 'none',
    color: '#ef4444',
    border: 'none',
    padding: '0 4px',
    fontSize: 14,
    cursor: 'pointer',
  },
}
