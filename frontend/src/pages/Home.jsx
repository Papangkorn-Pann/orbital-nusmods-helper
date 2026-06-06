import { Link } from 'react-router-dom'

// AY2025/2026 CourseReg rounds (Semester 1 & 2)
const ROUNDS = {
  sem1: [
    { round: 'Round 0',     dates: '7 – 11 Jul 2025',    who: 'Students with special circumstances / LOA returns' },
    { round: 'Round 1A',    dates: '14 – 18 Jul 2025',   who: 'Final-year students & those with the most AUs remaining' },
    { round: 'Round 1B',    dates: '21 – 25 Jul 2025',   who: 'All eligible undergraduate students' },
    { round: 'Round 2',     dates: '28 Jul – 1 Aug 2025',who: 'Remaining vacancies open to all' },
    { round: 'Add / Drop',  dates: '11 – 29 Aug 2025',   who: 'First two weeks of semester — swap without penalty' },
  ],
  sem2: [
    { round: 'Round 0',     dates: '10 – 14 Nov 2025',   who: 'Students with special circumstances / LOA returns' },
    { round: 'Round 1A',    dates: '17 – 21 Nov 2025',   who: 'Final-year students & those with the most AUs remaining' },
    { round: 'Round 1B',    dates: '24 – 28 Nov 2025',   who: 'All eligible undergraduate students' },
    { round: 'Round 2',     dates: '1 – 5 Dec 2025',     who: 'Remaining vacancies open to all' },
    { round: 'Add / Drop',  dates: '12 – 30 Jan 2026',   who: 'First two weeks of semester — swap without penalty' },
  ],
}

const FEATURES = [
  {
    icon: '📅',
    title: 'Timetable Builder',
    desc: 'Search any NUSMods module and pick your tutorial and lab slots. Auto-Generate finds the top 5 conflict-free timetables ranked by your preferences. Share a link with friends.',
    to: '/timetable',
    cta: 'Open Timetable',
  },
  {
    icon: '🔍',
    title: 'Module Analysis',
    desc: 'Enter any module code to see NLP-powered difficulty ratings, recommendation scores, and GPA outcomes extracted from real student reviews on NUSMods.',
    to: '/analysis',
    cta: 'Analyse a Module',
  },
  {
    icon: '⏱',
    title: 'Study Timer',
    desc: 'Track study hours with a one-click timer. Compare yourself against your faculty or year group on the anonymous leaderboard.',
    to: '/timer',
    cta: 'Start Studying',
  },
  {
    icon: '🧠',
    title: 'Study Plan (SM-2)',
    desc: 'Enter your exam dates and topics. The SM-2 spaced-repetition algorithm schedules daily review cards so you retain everything by exam day. Export to calendar.',
    to: '/studyplan',
    cta: 'Build My Plan',
  },
]

function RoundTable({ rounds }) {
  const today = new Date()
  return (
    <table style={tbl.table}>
      <thead>
        <tr>
          <th style={tbl.th}>Round</th>
          <th style={tbl.th}>Dates</th>
          <th style={tbl.th}>Eligible students</th>
        </tr>
      </thead>
      <tbody>
        {rounds.map(r => (
          <tr key={r.round} style={tbl.tr}>
            <td style={tbl.roundCell}>{r.round}</td>
            <td style={tbl.dateCell}>{r.dates}</td>
            <td style={tbl.whoCell}>{r.who}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

export default function Home() {
  return (
    <div className="page">
      {/* Hero */}
      <div style={s.hero}>
        <h1 style={s.heroTitle}>Plan smarter.<br />Study better.</h1>
        <p style={s.heroCopy}>
          An all-in-one companion for NUS students — from CourseReg day to final exams.
        </p>
        <Link to="/timetable">
          <button className="btn-primary" style={{ padding: '12px 32px', fontSize: 16 }}>
            Build my timetable →
          </button>
        </Link>
      </div>

      {/* Feature cards */}
      <div style={s.featureGrid}>
        {FEATURES.map(f => (
          <div key={f.title} className="card" style={s.featureCard}>
            <div style={s.featureIcon}>{f.icon}</div>
            <h2 style={s.featureTitle}>{f.title}</h2>
            <p style={s.featureDesc}>{f.desc}</p>
            <Link to={f.to}>
              <button className="btn-primary" style={{ width: '100%', marginTop: 'auto' }}>{f.cta}</button>
            </Link>
          </div>
        ))}
      </div>

      {/* CourseReg schedule */}
      <div style={s.section}>
        <h2 style={s.sectionTitle}>AY2025/2026 CourseReg Schedule</h2>
        <p style={s.sectionSub}>
          NUS uses a priority-based round system. Use the Timetable Builder to plan your bids before each round opens.
        </p>

        <div style={s.semGrid}>
          <div>
            <h3 style={s.semLabel}>Semester 1</h3>
            <RoundTable rounds={ROUNDS.sem1} />
          </div>
          <div>
            <h3 style={s.semLabel}>Semester 2</h3>
            <RoundTable rounds={ROUNDS.sem2} />
          </div>
        </div>

        <div style={s.tip}>
          <strong>💡 Tip:</strong> In Round 1A/1B, vacancies are allocated by priority. Having a backup slot ready increases your chance of getting a good timetable.
        </div>
      </div>
    </div>
  )
}

const s = {
  hero: {
    background: 'linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%)',
    borderRadius: 16,
    padding: '56px 48px',
    color: 'white',
    marginBottom: 32,
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
    alignItems: 'flex-start',
  },
  heroTitle: { fontSize: 40, fontWeight: 800, lineHeight: 1.15, margin: 0 },
  heroCopy: { fontSize: 17, opacity: 0.85, maxWidth: 480, margin: 0 },
  featureGrid: { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 20, marginBottom: 40 },
  featureCard: { display: 'flex', flexDirection: 'column', gap: 10 },
  featureIcon: { fontSize: 36 },
  featureTitle: { fontWeight: 700, fontSize: 18 },
  featureDesc: { color: '#64748b', fontSize: 14, lineHeight: 1.6, flex: 1 },
  section: { background: 'white', border: '1px solid #e2e8f0', borderRadius: 12, padding: 32 },
  sectionTitle: { fontWeight: 700, fontSize: 20, marginBottom: 8 },
  sectionSub: { color: '#64748b', fontSize: 14, marginBottom: 24 },
  semGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 32 },
  semLabel: { fontWeight: 700, fontSize: 15, marginBottom: 10, color: '#1e293b' },
  tip: {
    marginTop: 20,
    background: '#eff6ff',
    border: '1px solid #bfdbfe',
    borderRadius: 8,
    padding: '12px 16px',
    fontSize: 14,
    color: '#1e40af',
  },
}

const tbl = {
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 13 },
  th: {
    textAlign: 'left',
    padding: '8px 10px',
    background: '#f8fafc',
    color: '#64748b',
    fontWeight: 600,
    fontSize: 11,
    textTransform: 'uppercase',
    borderBottom: '2px solid #e2e8f0',
  },
  tr: { borderBottom: '1px solid #f1f5f9' },
  roundCell: { padding: '10px 10px', fontWeight: 700, color: '#2563eb', whiteSpace: 'nowrap' },
  dateCell: { padding: '10px 10px', color: '#374151', whiteSpace: 'nowrap' },
  whoCell: { padding: '10px 10px', color: '#64748b' },
}
