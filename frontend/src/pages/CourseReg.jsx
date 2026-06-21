import { useState } from 'react'
import { searchModules, getCourseRegAnalysis } from '../api.js'

// ── Subcomponents ─────────────────────────────────────────────────────────────

function CompetitionBar({ score }) {
  const pct   = Math.round(score * 100)
  const color = pct > 65 ? '#ef4444' : pct > 35 ? '#f59e0b' : '#22c55e'
  const label = pct > 65 ? 'High'    : pct > 35 ? 'Moderate' : 'Low'
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
        <span style={{ fontSize: 11, fontWeight: 700, color }}>{label}</span>
        <span style={{ fontSize: 11, color: '#94a3b8' }}>{pct}%</span>
      </div>
      <div style={s.barTrack}>
        <div style={{ ...s.barFill, width: pct + '%', background: color }} />
      </div>
    </div>
  )
}

function ProbBadge({ label, prob }) {
  const pct   = Math.round(prob * 100)
  const color = pct >= 70 ? '#16a34a' : pct >= 50 ? '#d97706' : '#dc2626'
  return (
    <div style={s.probCell}>
      <div style={{ fontSize: 15, fontWeight: 800, color }}>{pct}%</div>
      <div style={{ fontSize: 10, color: '#94a3b8', fontWeight: 500, whiteSpace: 'nowrap' }}>{label}</div>
    </div>
  )
}

function SlotCard({ slot }) {
  return (
    <div style={s.card}>
      <div style={s.cardHeader}>
        <span style={s.classNo}>Class {slot.class_no}</span>
        <span style={s.cap}>Cap: {slot.capacity}</span>
        {slot.platform_demand > 0 && (
          <span style={s.demandBadge}>
            {slot.platform_demand} user{slot.platform_demand !== 1 ? 's' : ''} bidding
          </span>
        )}
      </div>

      {/* Timing rows */}
      <div style={s.timings}>
        {slot.slots.map((t, i) => (
          <div key={i} style={s.timingRow}>
            <span style={s.timingDay}>{t.day?.slice(0, 3)}</span>
            <span style={s.timingTime}>
              {t.startTime?.slice(0, 2)}:{t.startTime?.slice(2)}–{t.endTime?.slice(0, 2)}:{t.endTime?.slice(2)}
            </span>
            {t.venue && <span style={s.venue}>{t.venue}</span>}
          </div>
        ))}
      </div>

      {/* Competition bar */}
      <div>
        <div style={s.sectionLabel}>Competition</div>
        <CompetitionBar score={slot.competition_score} />
      </div>

      {/* Round probabilities */}
      <div style={s.probRow}>
        <ProbBadge label="Rd 0"  prob={slot.round_probabilities.round_0}  />
        <ProbBadge label="Rd 1A" prob={slot.round_probabilities.round_1a} />
        <ProbBadge label="Rd 1B" prob={slot.round_probabilities.round_1b} />
        <ProbBadge label="Rd 2"  prob={slot.round_probabilities.round_2}  />
      </div>

      <p style={s.rec}>{slot.recommendation}</p>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

const LESSON_ORDER = ['Lecture', 'Tutorial', 'Lab', 'Sectional Teaching', 'Recitation', 'Workshop']

export default function CourseReg() {
  const [query,   setQuery]   = useState('')
  const [sugg,    setSugg]    = useState([])
  const [sem,     setSem]     = useState(1)
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState('')

  async function handleChange(e) {
    const q = e.target.value
    setQuery(q)
    if (q.length >= 2) {
      try { setSugg((await searchModules(q)).slice(0, 8)) }
      catch { setSugg([]) }
    } else {
      setSugg([])
    }
  }

  async function fetchAnalysis(code, s = sem) {
    if (!code.trim()) return
    setLoading(true)
    setError('')
    setData(null)
    setSugg([])
    try {
      const res = await getCourseRegAnalysis(code.toUpperCase().trim(), s)
      setData(res)
    } catch {
      setError('Module not found or has no timetable data for this semester.')
    } finally {
      setLoading(false)
    }
  }

  function pick(code) {
    setQuery(code)
    setSugg([])
    fetchAnalysis(code)
  }

  function handleBlur() { setTimeout(() => setSugg([]), 150) }

  function switchSem(n) {
    setSem(n)
    if (query.trim()) fetchAnalysis(query.trim(), n)
  }

  return (
    <div className="page">
      <h1 className="page-title">CourseReg Advisor</h1>
      <p style={s.sub}>
        See estimated slot competition and bid-success probabilities for any module.
        Scores use slot capacity, timing desirability, and live demand from users of
        this platform — so the more students plan here, the sharper the estimates get.
      </p>

      {/* Search bar + sem switcher */}
      <div style={s.topBar}>
        <div style={s.searchWrap}>
          <input
            value={query}
            onChange={handleChange}
            onBlur={handleBlur}
            placeholder="e.g. CS2040S, MA1521, GEA1000"
            style={s.input}
            autoComplete="off"
            onKeyDown={e => { if (e.key === 'Enter') { setSugg([]); fetchAnalysis(query) } }}
          />
          {sugg.length > 0 && (
            <div style={s.dropdown}>
              {sugg.map(m => (
                <div key={m.moduleCode} style={s.dropItem} onMouseDown={() => pick(m.moduleCode)}>
                  <span style={s.dropCode}>{m.moduleCode}</span>
                  <span style={s.dropTitle}>{m.title}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div style={{ display: 'flex', gap: 6 }}>
          {[1, 2].map(n => (
            <button
              key={n}
              className={sem === n ? 'btn-primary' : 'btn-ghost'}
              style={{ padding: '9px 18px' }}
              onClick={() => switchSem(n)}
            >
              Sem {n}
            </button>
          ))}
        </div>

        <button
          className="btn-primary"
          disabled={loading || !query.trim()}
          onClick={() => fetchAnalysis(query.trim())}
          style={{ padding: '9px 22px' }}
        >
          {loading ? 'Loading…' : 'Analyse'}
        </button>
      </div>

      {error && <p style={s.error}>{error}</p>}

      {/* Results */}
      {data && (
        <div>
          <div style={s.moduleBar}>
            <span style={s.moduleCode}>{data.module_code}</span>
            <span style={s.semBadge}>Sem {data.sem}</span>
          </div>
          <p style={s.note}>{data.note}</p>

          {/* Legend */}
          <div className="card" style={s.legend}>
            <h3 style={s.legendTitle}>How to read this</h3>
            <div style={s.legendItems}>
              <div><span style={{ color: '#22c55e', fontWeight: 700 }}>Low competition</span> — most students secure this slot in Round 2</div>
              <div><span style={{ color: '#f59e0b', fontWeight: 700 }}>Moderate competition</span> — Round 1B is usually sufficient</div>
              <div><span style={{ color: '#ef4444', fontWeight: 700 }}>High competition</span> — bid in Round 1A or 1B to be safe</div>
              <div style={{ marginTop: 4, color: '#94a3b8' }}>Probabilities show your estimated chance of successfully bidding each round.</div>
            </div>
          </div>

          {/* Lesson type sections */}
          {Object.entries(data.by_lesson_type)
            .sort(([a], [b]) => {
              const ai = LESSON_ORDER.indexOf(a)
              const bi = LESSON_ORDER.indexOf(b)
              return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi)
            })
            .map(([lt, slots]) => (
              <div key={lt} style={s.ltSection}>
                <h2 style={s.ltTitle}>{lt}</h2>
                <div style={s.slotGrid}>
                  {slots.map(slot => (
                    <SlotCard key={slot.class_no} slot={slot} />
                  ))}
                </div>
              </div>
            ))
          }
        </div>
      )}
    </div>
  )
}

// ── Styles ────────────────────────────────────────────────────────────────────

const s = {
  sub: { color: 'var(--text-muted)', fontSize: 13, marginBottom: 24, maxWidth: 620, lineHeight: 1.65 },
  topBar: { display: 'flex', gap: 10, marginBottom: 24, alignItems: 'flex-start', flexWrap: 'wrap' },
  searchWrap: { position: 'relative', flex: 1, minWidth: 200, maxWidth: 460 },
  input: {
    padding: '9px 14px', fontSize: 14,
    borderRadius: 'var(--radius)', border: '1.5px solid var(--border)',
    width: '100%',
  },
  dropdown: {
    position: 'absolute', top: '100%', left: 0, right: 0,
    background: 'white', border: '1px solid var(--border)', borderTop: 'none',
    borderRadius: '0 0 8px 8px', boxShadow: '0 4px 12px rgba(0,0,0,.12)', zIndex: 50,
  },
  dropItem: { padding: '9px 14px', cursor: 'pointer', display: 'flex', gap: 10, alignItems: 'center' },
  dropCode: { fontWeight: 700, color: 'var(--primary)', fontSize: 13, minWidth: 75, flexShrink: 0 },
  dropTitle: { fontSize: 12, color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  error: { color: '#ef4444', marginBottom: 16, fontSize: 14, fontWeight: 500 },
  moduleBar: { display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 },
  moduleCode: { fontWeight: 800, fontSize: 22, color: 'var(--primary)' },
  semBadge: {
    background: 'var(--border-light)', border: '1px solid var(--border)',
    borderRadius: 4, padding: '2px 8px', fontSize: 12,
    color: 'var(--text-muted)', fontWeight: 600,
  },
  note: { fontSize: 12, color: '#94a3b8', marginBottom: 20, maxWidth: 640, fontStyle: 'italic' },
  legend: { marginBottom: 24, padding: '14px 18px' },
  legendTitle: { fontWeight: 700, fontSize: 13, marginBottom: 10, color: '#1e293b' },
  legendItems: { display: 'flex', flexDirection: 'column', gap: 5, fontSize: 12, color: 'var(--text-muted)' },
  ltSection: { marginBottom: 28 },
  ltTitle: {
    fontWeight: 700, fontSize: 15, color: '#1e293b',
    marginBottom: 12, paddingBottom: 8, borderBottom: '1px solid var(--border)',
  },
  slotGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
    gap: 14,
  },
  card: {
    background: 'white', border: '1px solid var(--border)',
    borderRadius: 'var(--radius)', padding: '14px 16px',
    display: 'flex', flexDirection: 'column', gap: 10,
  },
  cardHeader: { display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' },
  classNo: { fontWeight: 700, fontSize: 14, color: 'var(--text)' },
  cap: { fontSize: 11, color: '#94a3b8' },
  demandBadge: {
    fontSize: 11, color: '#2563eb', fontWeight: 600,
    background: '#eff6ff', borderRadius: 4, padding: '1px 6px',
  },
  timings: { display: 'flex', flexDirection: 'column', gap: 3 },
  timingRow: { display: 'flex', gap: 8, fontSize: 12, alignItems: 'center' },
  timingDay: { fontWeight: 600, color: '#475569', minWidth: 30 },
  timingTime: { color: 'var(--text-muted)', fontVariantNumeric: 'tabular-nums' },
  venue: { color: '#94a3b8', fontSize: 11 },
  sectionLabel: {
    fontSize: 10, fontWeight: 700, color: '#475569',
    textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 4,
  },
  barTrack: { height: 6, background: '#f1f5f9', borderRadius: 3, overflow: 'hidden' },
  barFill: { height: '100%', borderRadius: 3, transition: 'width .4s ease' },
  probRow: {
    display: 'flex', justifyContent: 'space-around', flexWrap: 'nowrap',
    gap: 4, padding: '10px 4px', background: '#f8fafc', borderRadius: 6,
  },
  probCell: { textAlign: 'center', minWidth: 50, flex: '1 1 0' },
  rec: { fontSize: 11, color: '#64748b', margin: 0, fontStyle: 'italic', textAlign: 'center' },
}
