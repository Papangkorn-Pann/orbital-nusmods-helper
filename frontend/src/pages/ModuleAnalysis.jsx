import { useState, useEffect, useRef} from 'react'
import { getCourseInfo, searchModules, getEasiestModules, getMostRecommended } from '../api.js'

// ── Subcomponents ─────────────────────────────────────────────────────────────

function DifficultyGauge({ score }) {
  if (score == null) return <span style={{ color: '#94a3b8' }}>N/A</span>
  const pct  = ((score - 1) / 4) * 100
  const color = score <= 2 ? '#22c55e' : score <= 3.5 ? '#f59e0b' : '#ef4444'
  const label = score <= 2 ? 'Easy' : score <= 3.5 ? 'Medium' : 'Hard'
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
        <span style={{ fontWeight: 800, fontSize: 28, color }}>{score.toFixed(1)}</span>
        <span style={{ ...s.badge, background: color + '20', color }}>{label}</span>
      </div>
      <div style={s.barTrack}>
        <div style={{ ...s.barFill, width: pct + '%', background: color }} />
      </div>
      <div style={s.barLabels}><span>1 Easy</span><span>5 Hard</span></div>
    </div>
  )
}

function gpaToLetter(gpa) {
  if (gpa >= 5.0) return 'A'
  if (gpa >= 4.5) return 'A-'
  if (gpa >= 4.0) return 'B+'
  if (gpa >= 3.5) return 'B'
  if (gpa >= 3.0) return 'B-'
  if (gpa >= 2.5) return 'C+'
  if (gpa >= 2.0) return 'C'
  if (gpa >= 1.5) return 'D+'
  if (gpa >= 1.0) return 'D'
  return 'F'
}

function RecommendGauge({ score }) {
  if (score == null) return <span style={{ color: '#94a3b8' }}>N/A</span>
  const pct   = score * 100
  const color = pct >= 70 ? '#22c55e' : pct >= 40 ? '#f59e0b' : '#ef4444'
  const label = pct >= 70 ? 'Recommended' : pct >= 40 ? 'Mixed reviews' : 'Not recommended'
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
        <span style={{ fontWeight: 800, fontSize: 28, color }}>{pct.toFixed(0)}%</span>
        <span style={{ ...s.badge, background: color + '20', color }}>{label}</span>
      </div>
      <div style={s.barTrack}>
        <div style={{ ...s.barFill, width: pct + '%', background: color }} />
      </div>
    </div>
  )
}

function ReviewSummary({ summary, gradeThresholds, commentCount }) {
  if (commentCount === 0) return (
    <div className="card" style={{ textAlign: 'center', padding: '28px 20px' }}>
      <p style={{ color: 'var(--text-muted)', fontSize: 14, margin: 0 }}>
        No student reviews found on NUSMods for this module.
        Scores above are unavailable without review data.
      </p>
    </div>
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="card">
        <h3 style={s.statTitle}>Student Review Summary</h3>
        {summary
          ? <p style={{ fontSize: 14, color: 'var(--text)', lineHeight: 1.7, margin: 0 }}>{summary}</p>
          : <p style={{ fontSize: 14, color: 'var(--text-muted)', fontStyle: 'italic', lineHeight: 1.7, margin: 0 }}>
              AI summary is being generated — check back shortly.
            </p>}
      </div>

      {gradeThresholds && Object.keys(gradeThresholds).length > 0 && (
        <div className="card">
          <h3 style={s.statTitle}>Self-Reported Grade Thresholds</h3>
          <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 14 }}>
            Scores students reported achieving for each grade, extracted from reviews.
          </p>
          <div style={s.gradeTable}>
            {Object.entries(gradeThresholds).map(([grade, score]) => {
              const pct = Math.min(100, Math.max(0, (score - 40) / 60 * 100))
              const color = score >= 80 ? '#16a34a' : score >= 65 ? '#d97706' : '#dc2626'
              return (
                <div key={grade} style={s.gradeRow}>
                  <span style={s.gradeLabel}>{grade}</span>
                  <div style={s.gradeBarTrack}>
                    <div style={{ ...s.gradeBarFill, width: pct + '%', background: color }} />
                  </div>
                  <span style={{ ...s.gradeScore, color }}>{score}%</span>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

function AnalysisResult({ data }) {
  return (
    <div style={s.resultWrap}>
      {/* Module header */}
      <div className="card" style={s.headerCard}>
        <div style={s.moduleHeader}>
          <div>
            <span style={s.moduleCode}>{data.module}</span>
            <h2 style={s.moduleTitle}>{data.title}</h2>
          </div>
          <div style={s.metaBadges}>
            {data.module_credits && (
              <span style={s.creditBadge}>{data.module_credits} MCs</span>
            )}
            {data.department && (
              <span style={s.deptBadge}>{data.department}</span>
            )}
          </div>
        </div>
        {data.description && <p style={s.desc}>{data.description}</p>}


        <p style={s.commentCount}>
          Based on <strong>{data.comment_count ?? 0}</strong> student reviews from NUSMods
        </p>
      </div>

      {/* Scores grid */}
      <div style={s.scoreGrid}>
        <div className="card">
          <h3 style={s.statTitle}>Difficulty</h3>
          <DifficultyGauge score={data.difficulty_score} />
        </div>
        <div className="card">
          <h3 style={s.statTitle}>Recommendation</h3>
          <RecommendGauge score={data.recommend_score} />
        </div>
        <div className="card">
          <h3 style={s.statTitle}>Grade Outcomes</h3>
          <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 10 }}>
            Self-reported expected vs actual grade per student
          </p>
          {!data.grade_pairs || data.grade_pairs.length === 0 ? (
            <p style={{ color: '#94a3b8', fontSize: 13 }}>
              No grade mentions found in reviews
            </p>
          ) : (
            <div>
              <div style={s.pairsHeader}>
                <span style={s.pairsHdr}>#</span>
                <span style={s.pairsHdr}>Expected</span>
                <span style={s.pairsHdr}>Got</span>
              </div>
              {data.grade_pairs.map((p, i) => (
                <div key={i} style={s.pairsRow}>
                  <span style={s.pairsIdx}>{i + 1}</span>
                  <span style={{ ...s.pairsGrade, color: p.expected ? '#2563eb' : '#94a3b8' }}>
                    {p.expected ?? '—'}
                  </span>
                  <span style={{ ...s.pairsGrade, color: p.actual ? '#16a34a' : '#94a3b8' }}>
                    {p.actual ?? '—'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <ReviewSummary
        summary={data.summary}
        gradeThresholds={data.grade_thresholds}
        commentCount={data.comment_count ?? 0}
      />
    </div>
  )
}

// ── Top Modules discovery panel ───────────────────────────────────────────────

function TopModulesPanel({ onSelect }) {
  const [easiest,     setEasiest]     = useState(null)
  const [recommended, setRecommended] = useState(null)
  const [tab,         setTab]         = useState('easy')
  const [hoveredRow,  setHoveredRow]  = useState(null)

  useEffect(() => {
    getEasiestModules(5).then(setEasiest).catch(() => setEasiest([]))
    getMostRecommended(5).then(setRecommended).catch(() => setRecommended([]))
  }, [])

  const rows = (tab === 'easy' ? easiest : recommended) ?? null

  return (
    <div className="card" style={{ marginBottom: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
        <h3 style={s.statTitle}>Top Modules (from cached reviews)</h3>
        <div style={{ display: 'flex', gap: 6 }}>
          <button
            className={tab === 'easy' ? 'btn-primary' : 'btn-ghost'}
            style={{ padding: '4px 14px', fontSize: 12 }}
            onClick={() => setTab('easy')}
          >Easiest</button>
          <button
            className={tab === 'rec' ? 'btn-primary' : 'btn-ghost'}
            style={{ padding: '4px 14px', fontSize: 12 }}
            onClick={() => setTab('rec')}
          >Most Recommended</button>
        </div>
      </div>

      {rows === null && (
        <p style={{ color: '#94a3b8', fontSize: 13, textAlign: 'center', padding: 12 }}>Loading…</p>
      )}
      {rows !== null && rows.length === 0 && (
        <p style={{ color: '#94a3b8', fontSize: 13, textAlign: 'center', padding: 12 }}>
          No data yet — analyse some modules first to populate this list.
        </p>
      )}
      {rows !== null && rows.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {rows.slice(0, 8).map(m => (
            <div
              key={m.module_code}
              style={{ ...s.topRow, background: hoveredRow === m.module_code ? '#f1f5f9' : 'transparent' }}
              onClick={() => onSelect(m.module_code)}
              onMouseEnter={() => setHoveredRow(m.module_code)}
              onMouseLeave={() => setHoveredRow(null)}
            >
              <span style={s.topCode}>{m.module_code}</span>
              <span style={s.topTitle}>{m.title}</span>
              <span style={s.topStat}>
                {tab === 'easy'
                  ? (m.difficulty_score?.toFixed(1) ?? '—')
                  : (m.recommendation_score != null ? (m.recommendation_score * 100).toFixed(0) + '%' : '—')
                }
              </span>
              <span style={s.topCount}>{m.comment_count} reviews</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function ModuleAnalysis() {
  const [query,       setQuery]       = useState('')
  const [suggestions, setSuggestions] = useState([])
  const [result,      setResult]      = useState(null)
  const [loading,     setLoading]     = useState(false)
  const [error,       setError]       = useState('')
  const [hoveredIdx,  setHoveredIdx]  = useState(-1)
  const searchTimeout = useRef(null)

  async function analyze(code) {
    setLoading(true)
    setError('')
    setResult(null)
    setSuggestions([])
    try {
      const data = await getCourseInfo(code.toUpperCase().trim())
      setResult(data)
    } catch {
      setError('Module not found, has no Disqus reviews, or an error occurred.')
    } finally {
      setLoading(false)
    }
  }

  //TODO: fix lag
  async function handleQueryChange(e) {
    const q = e.target.value
    setQuery(q)
    clearTimeout(searchTimeout.current)
    if (q.length >= 2) { //two letters = length of most faculty code of module
      searchTimeout.current = setTimeout(async () => {
        try {
          const res = await searchModules(q)
          setSuggestions(res.slice(0, 8))
        } catch {
          setSuggestions([])
        }
      }, 250) //wait 1/4 of sec of the user not typing before fetching results
    } else {
      setSuggestions([])
    }
  }

  function handleSubmit(e) {
    e.preventDefault()
    if (query.trim()) {
      setSuggestions([])
      analyze(query.trim())
    }
  }

  function selectSuggestion(code) {
    setQuery(code)
    setSuggestions([])
    setHoveredIdx(-1)
    analyze(code)
  }

  function handleBlur() {
    setTimeout(() => setSuggestions([]), 150)
  }

  return (
    <div className="page">
      <h1 className="page-title">Module Analysis</h1>
      <p style={s.sub}>
        Enter any NUS module code to see NLP-powered difficulty, recommendation,
        and GPA analysis from real student reviews on NUSMods.
      </p>

      <TopModulesPanel onSelect={code => { setQuery(code); analyze(code) }} />

      {/* Search bar */}
      <form onSubmit={handleSubmit} style={s.searchForm}>
        <div style={s.searchWrap}>
          <input
            value={query}
            onChange={handleQueryChange}
            onBlur={handleBlur}
            placeholder="e.g. CS2040S, GEA1000, MA2001, IS1108"
            style={s.searchInput}
            autoComplete="off"
          />
          {suggestions.length > 0 && (
            <div style={s.dropdown}>
              {suggestions.map((m, i) => (
                <div
                  key={m.moduleCode}
                  style={{
                    ...s.dropItem,
                    background: hoveredIdx === i ? '#f1f5f9' : 'transparent',
                  }}
                  onMouseEnter={() => setHoveredIdx(i)}
                  onMouseLeave={() => setHoveredIdx(-1)}
                  onMouseDown={() => selectSuggestion(m.moduleCode)}
                >
                  <span style={s.dropCode}>{m.moduleCode}</span>
                  <span style={s.dropTitle}>{m.title}</span>
                </div>
              ))}
            </div>
          )}
        </div>
        <button
          type="submit"
          className="btn-primary"
          disabled={loading || !query.trim()}
          style={{ padding: '10px 24px', fontSize: 15, flexShrink: 0 }}
        >
          {loading ? 'Analyzing…' : 'Analyze'}
        </button>
      </form>

      {error && <p style={s.error}>{error}</p>}

      {loading && (
        <div style={s.loadingBox}>
          <div style={s.spinner} />
          <p style={s.loadingText}>
            Running NLP analysis — this may take 30–60 s for a new module
          </p>
          <p style={{ color: '#94a3b8', fontSize: 12 }}>
            Fetching reviews · Sentiment analysis · Difficulty &amp; recommendation scoring
          </p>
        </div>
      )}

      {result && !loading && <AnalysisResult data={result} />}
    </div>
  )
}

// ── Styles ────────────────────────────────────────────────────────────────────

const s = {
  sub: { color: 'var(--text-muted)', fontSize: 13, marginBottom: 24, maxWidth: 580, lineHeight: 1.6 },
  searchForm: { display: 'flex', gap: 10, marginBottom: 24, alignItems: 'flex-start' },
  searchWrap: { position: 'relative', flex: 1, maxWidth: 520 },
  searchInput: { padding: '10px 14px', fontSize: 15, borderRadius: 8, border: '1.5px solid #e2e8f0' },
  dropdown: {
    position: 'absolute', top: '100%', left: 0, right: 0,
    background: 'white', border: '1px solid #e2e8f0', borderTop: 'none',
    borderRadius: '0 0 8px 8px',
    boxShadow: '0 4px 12px rgba(0,0,0,.12)', zIndex: 50,
  },
  dropItem: {
    padding: '10px 14px', cursor: 'pointer',
    display: 'flex', gap: 10, alignItems: 'center',
  },
  dropCode: { fontWeight: 700, color: '#2563eb', fontSize: 13, minWidth: 80, flexShrink: 0 },
  dropTitle: {
    color: '#64748b', fontSize: 13,
    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
  },
  error: { color: '#ef4444', marginBottom: 16, fontSize: 14, fontWeight: 500 },
  loadingBox: {
    display: 'flex', flexDirection: 'column', alignItems: 'center',
    gap: 12, padding: '60px 0',
  },
  spinner: {
    width: 40, height: 40,
    border: '4px solid #e2e8f0',
    borderTop: '4px solid #2563eb',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  loadingText: { color: '#374151', fontSize: 15, fontWeight: 500 },
  resultWrap: { display: 'flex', flexDirection: 'column', gap: 20 },
  headerCard: {},
  moduleHeader: {
    display: 'flex', justifyContent: 'space-between',
    alignItems: 'flex-start', marginBottom: 12,
  },
  moduleCode: {
    display: 'block', fontSize: 12, fontWeight: 700,
    color: '#2563eb', marginBottom: 6, letterSpacing: '0.05em',
  },
  moduleTitle: { fontWeight: 700, fontSize: 20, margin: 0, color: 'var(--text)', letterSpacing: '-0.3px' },
  metaBadges: { display: 'flex', gap: 8, flexShrink: 0, flexWrap: 'wrap' },
  creditBadge: {
    background: 'var(--border-light)', color: 'var(--primary)',
    fontWeight: 600, fontSize: 12, padding: '3px 8px', borderRadius: 4,
    border: '1px solid var(--border)',
  },
  deptBadge: {
    background: 'var(--border-light)', color: 'var(--text-muted)',
    fontSize: 12, padding: '3px 8px', borderRadius: 4,
    border: '1px solid var(--border)',
  },
  desc: { color: '#475569', fontSize: 14, lineHeight: 1.7, margin: '0 0 12px' },
  commentCount: { color: '#94a3b8', fontSize: 12, margin: 0 },
  scoreGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 },
  statTitle: { fontWeight: 700, fontSize: 14, marginBottom: 14, color: '#1e293b' },
  badge: { padding: '2px 7px', borderRadius: 4, fontSize: 11, fontWeight: 600 },
  barTrack: { height: 8, background: '#f1f5f9', borderRadius: 4, overflow: 'hidden', marginBottom: 4 },
  barFill: { height: '100%', borderRadius: 4, transition: 'width .4s ease' },
  barLabels: {
    display: 'flex', justifyContent: 'space-between',
    fontSize: 11, color: '#94a3b8', marginTop: 4,
  },
  gpaRow: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '8px 0', borderBottom: '1px solid #f1f5f9',
  },
  gpaLabel: { color: '#64748b', fontSize: 13 },
  gpaVal: { fontWeight: 800, fontSize: 16, color: '#1e293b' },
  pairsHeader: {
    display: 'grid', gridTemplateColumns: '24px 1fr 1fr',
    gap: 8, paddingBottom: 4, borderBottom: '1px solid var(--border)', marginBottom: 4,
  },
  pairsHdr: { fontSize: 10, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' },
  pairsRow: {
    display: 'grid', gridTemplateColumns: '24px 1fr 1fr',
    gap: 8, padding: '4px 0', borderBottom: '1px solid var(--border-light)',
  },
  pairsIdx: { fontSize: 11, color: 'var(--text-muted)' },
  pairsGrade: { fontSize: 13, fontWeight: 700 },
  gradeTable: { display: 'flex', flexDirection: 'column', gap: 8 },
  gradeRow: { display: 'grid', gridTemplateColumns: '36px 1fr 48px', gap: 10, alignItems: 'center' },
  gradeLabel: { fontWeight: 700, fontSize: 13, color: 'var(--text)' },
  gradeBarTrack: { height: 6, background: 'var(--border)', borderRadius: 3, overflow: 'hidden' },
  gradeBarFill: { height: '100%', borderRadius: 3, transition: 'width .4s' },
  gradeScore: { fontSize: 12, fontWeight: 600, textAlign: 'right' },
  workloadRow: {
    display: 'flex', gap: 0, margin: '12px 0',
    border: '1px solid var(--border)', borderRadius: 'var(--radius)',
    overflow: 'hidden',
  },
  workloadCell: {
    flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center',
    padding: '10px 6px', borderRight: '1px solid var(--border)',
  },
  workloadNum: { fontWeight: 700, fontSize: 16, color: 'var(--text)' },
  workloadLabel: { fontSize: 10, color: 'var(--text-muted)', marginTop: 2, textTransform: 'uppercase', letterSpacing: '0.05em' },
  reqRow: { display: 'flex', flexDirection: 'column', gap: 8, margin: '10px 0' },
  reqItem: { display: 'flex', gap: 10, alignItems: 'flex-start' },
  reqLabel: {
    fontSize: 11, fontWeight: 700, color: 'var(--text-muted)',
    textTransform: 'uppercase', letterSpacing: '0.05em',
    flexShrink: 0, paddingTop: 2, width: 90,
  },
  reqText: { fontSize: 13, color: 'var(--text)', lineHeight: 1.5 },
  topRow: {
    display: 'grid',
    gridTemplateColumns: '90px 1fr auto auto',
    gap: 10, alignItems: 'center',
    padding: '8px 10px', borderRadius: 6,
    cursor: 'pointer',
    transition: 'background .12s',
  },
  topCode:  { fontWeight: 700, color: '#2563eb', fontSize: 13 },
  topTitle: { fontSize: 13, color: '#374151', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  topStat:  { fontWeight: 700, fontSize: 13, color: '#1e293b', whiteSpace: 'nowrap' },
  topCount: { color: '#94a3b8', fontSize: 12, whiteSpace: 'nowrap' },
}
