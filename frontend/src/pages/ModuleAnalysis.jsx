import { useState } from 'react'
import { getCourseInfo, searchModules } from '../api.js'

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

function CommentCard({ comment, likes, sentiment }) {
  if (!comment) return null
  const colors = { positive: '#22c55e', neutral: '#f59e0b', negative: '#ef4444' }
  const labels = { positive: '👍 Positive', neutral: '😐 Neutral', negative: '👎 Negative' }
  const color  = colors[sentiment] || '#94a3b8'
  return (
    <div style={{ ...s.commentBox, borderLeft: `3px solid ${color}` }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <span style={{ color, fontSize: 12, fontWeight: 700 }}>{labels[sentiment]}</span>
        {likes != null && likes >= 0 && (
          <span style={{ color: '#94a3b8', fontSize: 12 }}>{likes} ♥</span>
        )}
      </div>
      <p style={s.commentText}>{comment}</p>
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
          <h3 style={s.statTitle}>GPA Outcomes</h3>
          {data.expected_gpa == null && data.actual_gpa == null ? (
            <p style={{ color: '#94a3b8', fontSize: 13 }}>
              No grade data found in reviews
            </p>
          ) : (
            <div>
              {data.expected_gpa != null && (
                <div style={s.gpaRow}>
                  <span style={s.gpaLabel}>Expected GPA</span>
                  <span style={s.gpaVal}>{data.expected_gpa.toFixed(2)}</span>
                </div>
              )}
              {data.actual_gpa != null && (
                <div style={s.gpaRow}>
                  <span style={s.gpaLabel}>Actual GPA</span>
                  <span style={s.gpaVal}>{data.actual_gpa.toFixed(2)}</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Top comments */}
      {(data.top_positive_comment_message ||
        data.top_neutral_comment_message  ||
        data.top_negative_comment_message) && (
        <div className="card">
          <h3 style={s.statTitle}>Top Student Comments</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <CommentCard
              comment={data.top_positive_comment_message}
              likes={data.top_positive_comment_likes}
              sentiment="positive"
            />
            <CommentCard
              comment={data.top_neutral_comment_message}
              likes={data.top_neutral_comment_likes}
              sentiment="neutral"
            />
            <CommentCard
              comment={data.top_negative_comment_message}
              likes={data.top_negative_comment_likes}
              sentiment="negative"
            />
          </div>
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

  async function handleQueryChange(e) {
    const q = e.target.value
    setQuery(q)
    if (q.length >= 2) {
      try {
        const res = await searchModules(q)
        setSuggestions(res.slice(0, 8))
      } catch {
        setSuggestions([])
      }
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
  sub: { color: '#64748b', fontSize: 14, marginBottom: 24, maxWidth: 580, lineHeight: 1.6 },
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
  moduleTitle: { fontWeight: 800, fontSize: 22, margin: 0, color: '#0f172a' },
  metaBadges: { display: 'flex', gap: 8, flexShrink: 0, flexWrap: 'wrap' },
  creditBadge: {
    background: '#eff6ff', color: '#1d4ed8',
    fontWeight: 700, fontSize: 13, padding: '4px 12px', borderRadius: 20,
  },
  deptBadge: {
    background: '#f8fafc', color: '#64748b',
    fontSize: 12, padding: '4px 12px', borderRadius: 20,
    border: '1px solid #e2e8f0',
  },
  desc: { color: '#475569', fontSize: 14, lineHeight: 1.7, margin: '0 0 12px' },
  commentCount: { color: '#94a3b8', fontSize: 12, margin: 0 },
  scoreGrid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 },
  statTitle: { fontWeight: 700, fontSize: 14, marginBottom: 14, color: '#1e293b' },
  badge: { padding: '3px 10px', borderRadius: 20, fontSize: 12, fontWeight: 700 },
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
  commentBox: { padding: '12px 14px', background: '#f8fafc', borderRadius: 8 },
  commentText: { fontSize: 13, color: '#374151', lineHeight: 1.65, margin: 0 },
}
