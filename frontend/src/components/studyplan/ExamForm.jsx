import { useState } from 'react'
import { addExam } from '../../api.js'

export default function ExamForm({ userId, onAdded }) {
  const [code,      setCode]      = useState('')
  const [examDate,  setExamDate]  = useState('')
  const [topics,    setTopics]    = useState('')
  const [loading,   setLoading]   = useState(false)
  const [error,     setError]     = useState('')

  async function handleSubmit(e) {
    e.preventDefault()
    const topicList = topics.split(',').map(t => t.trim()).filter(Boolean)
    if (!code || !examDate || topicList.length === 0) {
      setError('Fill in all fields and at least one topic.')
      return
    }
    setError('')
    setLoading(true)
    try {
      await addExam({ user_id: userId, module_code: code.toUpperCase(), topics: topicList, exam_date: examDate })
      setCode(''); setExamDate(''); setTopics('')
      onAdded()
    } catch {
      setError('Failed to add exam. Check the module code.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      <h3 style={styles.title}>Add Exam</h3>

      <div style={styles.row}>
        <div style={styles.field}>
          <label style={styles.label}>Module code</label>
          <input value={code} onChange={e => setCode(e.target.value.toUpperCase())} placeholder="CS2040S" />
        </div>
        <div style={styles.field}>
          <label style={styles.label}>Exam date</label>
          <input type="date" value={examDate} onChange={e => setExamDate(e.target.value)} />
        </div>
      </div>

      <div style={styles.field}>
        <label style={styles.label}>Topics <span style={styles.hint}>(comma-separated)</span></label>
        <input
          value={topics}
          onChange={e => setTopics(e.target.value)}
          placeholder="Sorting, Graphs, Dynamic Programming, Hash Tables"
        />
      </div>

      {error && <p style={styles.error}>{error}</p>}

      <button className="btn-primary" type="submit" disabled={loading} style={{ alignSelf: 'flex-start' }}>
        {loading ? 'Adding…' : '+ Add exam'}
      </button>
    </form>
  )
}

const styles = {
  form: { display: 'flex', flexDirection: 'column', gap: 14 },
  title: { fontWeight: 700, fontSize: 16 },
  row: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 },
  field: { display: 'flex', flexDirection: 'column', gap: 4 },
  label: { fontSize: 12, fontWeight: 600, color: '#374151' },
  hint: { fontWeight: 400, color: '#94a3b8' },
  error: { color: '#ef4444', fontSize: 13 },
}
