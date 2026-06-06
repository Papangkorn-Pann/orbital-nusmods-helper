import { useState, useEffect } from 'react'
import { getUserId } from '../App.jsx'
import {
  getTodayCards, getSchedule, getUser,
  deleteCard, deleteExam, exportStudyPlan,
} from '../api.js'
import ExamForm from '../components/studyplan/ExamForm.jsx'
import CardReviewer from '../components/studyplan/CardReviewer.jsx'

export default function StudyPlan() {
  const userId = getUserId()
  const [dueCards,  setDueCards]  = useState([])
  const [schedule,  setSchedule]  = useState([])
  const [tab,       setTab]       = useState('review')
  const [loading,   setLoading]   = useState(true)
  const [streak,    setStreak]    = useState(0)

  async function loadAll() {
    setLoading(true)
    try {
      const [t, s] = await Promise.all([
        getTodayCards(userId),
        getSchedule(userId),
      ])
      setDueCards(t.cards || [])
      setSchedule(s.cards || [])
    } finally {
      setLoading(false)
    }
    // Streak is non-critical; fetch separately so it never blocks
    getUser(userId)
      .then(u => setStreak(u?.review_streak || 0))
      .catch(() => {})
  }

  useEffect(() => { loadAll() }, [])

  async function handleDeleteCard(cardId) {
    if (!window.confirm('Delete this review card?')) return
    await deleteCard(cardId)
    loadAll()
  }

  async function handleDeleteExam(moduleCode) {
    if (!window.confirm(`Delete all cards for ${moduleCode}? This cannot be undone.`)) return
    await deleteExam(userId, moduleCode)
    loadAll()
  }

  // Group schedule by module + exam date
  const byExam = {}
  for (const card of schedule) {
    const key = `${card.module_code} — ${card.exam_date}`
    if (!byExam[key]) byExam[key] = { module_code: card.module_code, cards: [] }
    byExam[key].cards.push(card)
  }

  const today = new Date().toISOString().slice(0, 10)

  return (
    <div className="page">
      <div style={styles.topBar}>
        <h1 className="page-title" style={{ marginBottom: 0 }}>Study Plan</h1>
        <div style={styles.dueChip}>
          {dueCards.length} card{dueCards.length !== 1 ? 's' : ''} due today
        </div>
        {streak > 0 && (
          <div style={styles.streakChip} title="Consecutive days of review">
            🔥 {streak}-day streak
          </div>
        )}
      </div>

      {/* Tabs */}
      <div style={styles.tabs}>
        {[
          { id: 'review',   label: `Review${dueCards.length > 0 ? ` (${dueCards.length})` : ''}` },
          { id: 'add',      label: '+ Add Exam' },
          { id: 'schedule', label: 'Upcoming Schedule' },
        ].map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            style={{ ...styles.tab, ...(tab === t.id ? styles.tabActive : {}) }}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div style={styles.content}>
        {/* Review tab */}
        {tab === 'review' && !loading && (
          <CardReviewer cards={dueCards} onReviewed={loadAll} />
        )}

        {/* Add exam tab */}
        {tab === 'add' && (
          <div className="card">
            <ExamForm userId={userId} onAdded={() => { loadAll(); setTab('review') }} />
          </div>
        )}

        {/* Schedule tab */}
        {tab === 'schedule' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {schedule.length > 0 && (
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <button
                  className="btn-ghost"
                  onClick={() => exportStudyPlan(userId)}
                  style={{ fontSize: 13, padding: '7px 14px' }}
                >
                  📅 Export to Calendar (.ics)
                </button>
              </div>
            )}

            {schedule.length === 0 && (
              <p style={styles.empty}>No study cards yet. Add an exam to get started.</p>
            )}

            {Object.entries(byExam).map(([key, { module_code, cards }]) => (
              <div key={key} className="card">
                <div style={styles.examHeader}>
                  <h3 style={styles.examKey}>{key}</h3>
                  <button
                    className="btn-danger"
                    onClick={() => handleDeleteExam(module_code)}
                    style={{ padding: '4px 12px', fontSize: 12 }}
                  >
                    Delete Exam
                  </button>
                </div>
                <div style={styles.cardList}>
                  {cards.map(c => {
                    const overdue  = c.next_review_date < today
                    const dueToday = c.next_review_date === today
                    return (
                      <div key={c.id} style={styles.schedRow}>
                        <div style={styles.schedTopic}>{c.topic}</div>
                        <div style={{
                          ...styles.schedDate,
                          color: overdue ? '#ef4444' : dueToday ? '#f59e0b' : '#22c55e',
                        }}>
                          {overdue ? '⚠ ' : dueToday ? '📅 ' : '✓ '}
                          {c.next_review_date}
                        </div>
                        <div style={styles.schedInterval}>Every {c.interval_days}d</div>
                        <div style={styles.schedReps}>×{c.repetitions}</div>
                        <button
                          onClick={() => handleDeleteCard(c.id)}
                          style={styles.trashBtn}
                          title="Delete this card"
                        >
                          🗑
                        </button>
                      </div>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

const styles = {
  topBar: { display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20, flexWrap: 'wrap' },
  dueChip: {
    background: '#fef3c7', color: '#92400e',
    borderRadius: 20, padding: '4px 14px',
    fontWeight: 600, fontSize: 13,
  },
  streakChip: {
    background: '#fff7ed', color: '#c2410c',
    borderRadius: 20, padding: '4px 14px',
    fontWeight: 600, fontSize: 13,
  },
  tabs: { display: 'flex', gap: 4, marginBottom: 24, borderBottom: '1px solid #e2e8f0', paddingBottom: 0 },
  tab: {
    padding: '10px 20px', background: 'none', border: 'none',
    borderBottom: '3px solid transparent', borderRadius: 0,
    color: '#64748b', fontWeight: 500, cursor: 'pointer',
    fontSize: 14, marginBottom: -1,
  },
  tabActive: { color: '#2563eb', borderBottom: '3px solid #2563eb' },
  content: { maxWidth: 680, margin: '0 auto' },
  empty: { color: '#94a3b8', textAlign: 'center', padding: 40 },
  examHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  examKey: { fontWeight: 700, fontSize: 15, color: '#1e293b' },
  cardList: { display: 'flex', flexDirection: 'column', gap: 6 },
  schedRow: {
    display: 'grid',
    gridTemplateColumns: '1fr auto auto auto auto',
    gap: 10,
    alignItems: 'center',
    padding: '8px 0',
    borderBottom: '1px solid #f1f5f9',
    fontSize: 13,
  },
  schedTopic:    { fontWeight: 500 },
  schedDate:     { fontWeight: 600, fontSize: 12 },
  schedInterval: { color: '#94a3b8', fontSize: 12 },
  schedReps:     { color: '#94a3b8', fontSize: 12, textAlign: 'right' },
  trashBtn: {
    background: 'none', border: 'none', cursor: 'pointer',
    fontSize: 14, opacity: 0.45, padding: '2px 4px', borderRadius: 4,
  },
}
