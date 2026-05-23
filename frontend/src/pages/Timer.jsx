import { useState } from 'react'
import { getUserId } from '../App.jsx'
import { updateUser } from '../api.js'
import TimerWidget from '../components/timer/TimerWidget.jsx'
import Leaderboard from '../components/timer/Leaderboard.jsx'

const FACULTIES = ['SOC', 'FOS', 'FOE', 'BIZ', 'LAW', 'MED', 'DEN', 'FASS', 'CDE', 'YST', 'SPH']

export default function Timer() {
  const userId = getUserId()
  const [name, setName]       = useState(localStorage.getItem('displayName') || '')
  const [faculty, setFaculty] = useState(localStorage.getItem('faculty') || '')
  const [year, setYear]       = useState(localStorage.getItem('year') || '')
  const [saved, setSaved]     = useState(false)

  function saveProfile() {
    localStorage.setItem('displayName', name)
    localStorage.setItem('faculty', faculty)
    localStorage.setItem('year', year)
    updateUser(userId, {
      display_name: name || 'Anonymous',
      faculty: faculty || null,
      year_of_study: year ? parseInt(year) : null,
    })
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div className="page">
      <h1 className="page-title">Study Timer</h1>

      <div style={styles.layout}>
        {/* left: timer + profile */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          <TimerWidget userId={userId} />

          {/* profile card */}
          <div className="card">
            <h3 style={styles.cardTitle}>Your Profile</h3>
            <p style={styles.sub}>Shown anonymously on the leaderboard</p>
            <div style={styles.formGrid}>
              <label style={styles.label}>Display name</label>
              <input value={name} onChange={e => setName(e.target.value)} placeholder="Anonymous" />

              <label style={styles.label}>Faculty</label>
              <select value={faculty} onChange={e => setFaculty(e.target.value)}>
                <option value="">— Select —</option>
                {FACULTIES.map(f => <option key={f} value={f}>{f}</option>)}
              </select>

              <label style={styles.label}>Year of study</label>
              <select value={year} onChange={e => setYear(e.target.value)}>
                <option value="">— Select —</option>
                {[1,2,3,4,5].map(y => <option key={y} value={y}>Year {y}</option>)}
              </select>
            </div>
            <button className="btn-primary" onClick={saveProfile} style={{ marginTop: 16, width: '100%' }}>
              {saved ? '✓ Saved' : 'Save Profile'}
            </button>
          </div>
        </div>

        {/* right: leaderboard */}
        <div>
          <Leaderboard userId={userId} />
        </div>
      </div>
    </div>
  )
}

const styles = {
  layout: {
    display: 'grid',
    gridTemplateColumns: '380px 1fr',
    gap: 24,
    alignItems: 'start',
  },
  cardTitle: { fontWeight: 700, fontSize: 16, marginBottom: 4 },
  sub: { color: '#94a3b8', fontSize: 12, marginBottom: 16 },
  formGrid: { display: 'grid', gridTemplateColumns: '120px 1fr', gap: '10px 12px', alignItems: 'center' },
  label: { fontWeight: 500, color: '#374151', fontSize: 13 },
}
