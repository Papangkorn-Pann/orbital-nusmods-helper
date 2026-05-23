const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
const DAY_SHORT = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
const HOUR_START = 8   // 0800
const HOUR_END   = 22  // 2200
const SLOT_COUNT = (HOUR_END - HOUR_START) * 2  // 28 half-hour rows

const PALETTE = [
  '#3b82f6','#10b981','#f59e0b','#8b5cf6',
  '#ef4444','#06b6d4','#f97316','#6366f1',
  '#14b8a6','#ec4899','#84cc16','#a78bfa',
]

function getColor(code, codes) {
  const i = codes.indexOf(code)
  return PALETTE[i % PALETTE.length]
}

function timeToRow(t) {
  // t = "0930" → grid row (1-based, row 1 is the day header)
  const h = parseInt(t.slice(0, 2))
  const m = parseInt(t.slice(2, 4))
  return Math.floor((h * 60 + m - HOUR_START * 60) / 30) + 2
}

function dayToCol(day) {
  return DAYS.indexOf(day) + 2   // col 1 = time label
}

function formatTime(t) {
  return `${t.slice(0, 2)}:${t.slice(2, 4)}`
}

export default function TimetableGrid({ renderedSlots, moduleColors, onSlotClick }) {
  const moduleCodes = Object.keys(moduleColors)

  // Time labels on the left
  const timeLabels = []
  for (let i = 0; i < SLOT_COUNT; i++) {
    const totalMins = HOUR_START * 60 + i * 30
    const hh = String(Math.floor(totalMins / 60)).padStart(2, '0')
    const mm = String(totalMins % 60).padStart(2, '0')
    timeLabels.push(`${hh}:${mm}`)
  }

  return (
    <div style={styles.wrapper}>
      <div style={styles.grid}>
        {/* top-left empty cell */}
        <div style={{ gridColumn: 1, gridRow: 1 }} />

        {/* day headers */}
        {DAYS.map((day, i) => (
          <div key={day} style={{ ...styles.dayHeader, gridColumn: i + 2, gridRow: 1 }}>
            {DAY_SHORT[i]}
          </div>
        ))}

        {/* time labels + horizontal lines */}
        {timeLabels.map((label, i) => (
          <div key={label} style={{ ...styles.timeLabel, gridColumn: 1, gridRow: i + 2 }}>
            {i % 2 === 0 ? label : ''}
          </div>
        ))}

        {/* empty grid cells for the background lines */}
        {DAYS.map((day, di) =>
          timeLabels.map((_, ti) => (
            <div
              key={`${di}-${ti}`}
              style={{
                ...styles.cell,
                gridColumn: di + 2,
                gridRow: ti + 2,
                borderTop: ti % 2 === 0 ? '1px solid #e2e8f0' : '1px solid #f1f5f9',
              }}
            />
          ))
        )}

        {/* actual lesson blocks */}
        {renderedSlots.map((slot, i) => {
          const color = moduleColors[slot.moduleCode] || '#94a3b8'
          const col = dayToCol(slot.day)
          const rowStart = timeToRow(slot.startTime)
          const rowEnd   = timeToRow(slot.endTime)
          if (col < 2 || rowStart < 2) return null

          return (
            <div
              key={i}
              onClick={() => onSlotClick && onSlotClick(slot)}
              title={`${slot.moduleCode} ${slot.lessonType} [${slot.classNo}]\n${slot.venue}\n${formatTime(slot.startTime)}–${formatTime(slot.endTime)}`}
              style={{
                ...styles.slotBlock,
                gridColumn: col,
                gridRowStart: rowStart,
                gridRowEnd: rowEnd,
                background: color,
              }}
            >
              <div style={styles.slotCode}>{slot.moduleCode}</div>
              <div style={styles.slotType}>{slot.lessonType.replace('Tutorial', 'Tut').replace('Lecture', 'Lec').replace('Laboratory', 'Lab')}</div>
              <div style={styles.slotVenue}>{slot.venue}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

const ROW_H = 40   // px per 30-min slot
const styles = {
  wrapper: {
    overflowX: 'auto',
    border: '1px solid #e2e8f0',
    borderRadius: 8,
    background: 'white',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: `64px repeat(5, 1fr)`,
    gridTemplateRows: `36px repeat(${SLOT_COUNT}, ${ROW_H}px)`,
    minWidth: 700,
    position: 'relative',
  },
  dayHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 600,
    fontSize: 13,
    color: '#475569',
    borderBottom: '2px solid #e2e8f0',
    background: '#f8fafc',
  },
  timeLabel: {
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'center',
    fontSize: 10,
    color: '#94a3b8',
    paddingTop: 2,
    borderRight: '1px solid #e2e8f0',
  },
  cell: {
    borderRight: '1px solid #f1f5f9',
  },
  slotBlock: {
    margin: '2px 3px',
    borderRadius: 6,
    padding: '4px 6px',
    color: 'white',
    fontSize: 11,
    fontWeight: 600,
    overflow: 'hidden',
    cursor: 'pointer',
    display: 'flex',
    flexDirection: 'column',
    gap: 1,
    zIndex: 1,
    transition: 'opacity .15s, transform .15s',
  },
  slotCode:  { fontSize: 12, fontWeight: 700 },
  slotType:  { fontSize: 10, opacity: 0.9 },
  slotVenue: { fontSize: 10, opacity: 0.75, marginTop: 'auto' },
}
