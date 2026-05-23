import { useState } from 'react'

function formatTime(t) {
  return `${t.slice(0, 2)}:${t.slice(2, 4)}`
}

// Group raw slot array by classNo, returning first occurrence per class
function groupByClass(slots) {
  const map = {}
  for (const s of slots) {
    if (!map[s.classNo]) map[s.classNo] = s
  }
  return Object.values(map)
}

export default function SlotChooser({ moduleCode, lessonType, slots, selectedClassNo, color, onSelect }) {
  const [open, setOpen] = useState(false)
  const classes = groupByClass(slots)
  const current = classes.find(c => c.classNo === selectedClassNo) || classes[0]

  return (
    <div style={styles.container}>
      <div
        style={{ ...styles.header, borderLeft: `3px solid ${color}` }}
        onClick={() => setOpen(o => !o)}
      >
        <span style={styles.lessonType}>{lessonType}</span>
        {current && (
          <span style={styles.current}>
            [{current.classNo}] {current.day.slice(0,3)} {formatTime(current.startTime)}–{formatTime(current.endTime)} · {current.venue}
          </span>
        )}
        <span style={styles.chevron}>{open ? '▲' : '▼'}</span>
      </div>

      {open && (
        <div style={styles.dropdown}>
          {classes.map(c => (
            <div
              key={c.classNo}
              onClick={() => { onSelect(moduleCode, lessonType, c.classNo); setOpen(false) }}
              style={{
                ...styles.option,
                background: c.classNo === selectedClassNo ? '#dbeafe' : 'white',
                fontWeight: c.classNo === selectedClassNo ? 600 : 400,
              }}
            >
              <span style={styles.classNo}>[{c.classNo}]</span>
              <span>{c.day.slice(0,3)} {formatTime(c.startTime)}–{formatTime(c.endTime)}</span>
              <span style={styles.venue}>{c.venue}</span>
              {c.size && <span style={styles.size}>Cap {c.size}</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

const styles = {
  container: { marginBottom: 6 },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '6px 10px',
    background: '#f8fafc',
    borderRadius: 6,
    cursor: 'pointer',
    fontSize: 12,
    userSelect: 'none',
  },
  lessonType: { fontWeight: 600, color: '#374151', minWidth: 80 },
  current: { color: '#64748b', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  chevron: { color: '#94a3b8', fontSize: 10 },
  dropdown: {
    border: '1px solid #e2e8f0',
    borderRadius: 6,
    overflow: 'hidden',
    marginTop: 2,
    boxShadow: '0 4px 6px rgba(0,0,0,.06)',
  },
  option: {
    display: 'grid',
    gridTemplateColumns: '50px 1fr auto auto',
    gap: 8,
    padding: '8px 10px',
    cursor: 'pointer',
    fontSize: 12,
    alignItems: 'center',
    borderBottom: '1px solid #f1f5f9',
    transition: 'background .1s',
  },
  classNo: { fontWeight: 600, color: '#2563eb' },
  venue: { color: '#64748b' },
  size: { color: '#94a3b8', fontSize: 11 },
}
