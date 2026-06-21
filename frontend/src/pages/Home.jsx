import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'

// All CourseReg rounds with parseable start dates
const ROUND_DATES = [
  { label: 'Sem 1 Round 0',    date: new Date('2026-07-06') },
  { label: 'Sem 1 Round 1A',   date: new Date('2026-07-13') },
  { label: 'Sem 1 Round 1B',   date: new Date('2026-07-20') },
  { label: 'Sem 1 Round 2',    date: new Date('2026-07-27') },
  { label: 'Sem 1 Add/Drop',   date: new Date('2026-08-10') },
  { label: 'Sem 2 Round 0',    date: new Date('2026-11-09') },
  { label: 'Sem 2 Round 1A',   date: new Date('2026-11-16') },
  { label: 'Sem 2 Round 1B',   date: new Date('2026-11-23') },
  { label: 'Sem 2 Round 2',    date: new Date('2026-11-30') },
  { label: 'Sem 2 Add/Drop',   date: new Date('2027-01-11') },
]

function CourseRegCountdown() {
  const [info, setInfo] = useState(null)
  useEffect(() => {
    function compute() {
      const now = new Date()
      const upcoming = ROUND_DATES.filter(r => r.date >= now)
      if (upcoming.length === 0) { setInfo({ done: true }); return }
      const next = upcoming[0]
      const days = Math.ceil((next.date - now) / 86400000)
      setInfo({ label: next.label, days })
    }
    compute()
    const t = setInterval(compute, 60000)
    return () => clearInterval(t)
  }, [])

  if (!info) return null
  if (info.done) return (
    <div style={cd.wrap}>
      <span style={cd.label}>AY2026/2027 CourseReg</span>
      <span style={cd.val}>All rounds complete</span>
    </div>
  )
  return (
    <div style={cd.wrap}>
      <span style={cd.label}>Next: {info.label}</span>
      <span style={cd.val}>
        {info.days === 0 ? 'Today' : info.days === 1 ? 'Tomorrow' : `In ${info.days} days`}
      </span>
    </div>
  )
}

// AY2026/2027 CourseReg rounds (Semester 1 & 2)
const ROUNDS = {
  sem1: [
    { round: 'Round 0',     dates: '6 – 10 Jul 2026',    who: 'Students with special circumstances / LOA returns' },
    { round: 'Round 1A',    dates: '13 – 17 Jul 2026',   who: 'Final-year students & those with the most AUs remaining' },
    { round: 'Round 1B',    dates: '20 – 24 Jul 2026',   who: 'All eligible undergraduate students' },
    { round: 'Round 2',     dates: '27 Jul – 1 Aug 2026',who: 'Remaining vacancies open to all' },
    { round: 'Add / Drop',  dates: '10 – 28 Aug 2026',   who: 'First two weeks of semester — swap without penalty' },
  ],
  sem2: [
    { round: 'Round 0',     dates: '9 – 13 Nov 2026',    who: 'Students with special circumstances / LOA returns' },
    { round: 'Round 1A',    dates: '16 – 20 Nov 2026',   who: 'Final-year students & those with the most AUs remaining' },
    { round: 'Round 1B',    dates: '23 – 27 Nov 2026',   who: 'All eligible undergraduate students' },
    { round: 'Round 2',     dates: '30 Nov – 4 Dec 2026',who: 'Remaining vacancies open to all' },
    { round: 'Add / Drop',  dates: '11 – 29 Jan 2027',   who: 'First two weeks of semester — swap without penalty' },
  ],
}

const FEATURES = [
  {
    title: 'Timetable Builder',
    desc: 'Search any NUSMods module and pick your tutorial and lab slots. Auto-generate finds the top 5 conflict-free timetables ranked by your preferences. Share a link with friends.',
    to: '/timetable',
    cta: 'Open timetable',
  },
  {
    title: 'CourseReg Advisor',
    desc: 'See estimated slot competition and bid-success probabilities for every tutorial/lab slot. Powered by slot capacity, timing desirability, and live demand from platform users.',
    to: '/coursereg',
    cta: 'Plan my bids',
  },
  {
    title: 'Module Analysis',
    desc: 'Enter any module code to see NLP-powered difficulty ratings, recommendation scores, and GPA outcomes extracted from real student reviews on NUSMods.',
    to: '/analysis',
    cta: 'Analyse a module',
  },
  {
    title: 'Study Timer',
    desc: 'Track study hours with a one-click timer. Compare yourself against your faculty or year group on the anonymous weekly leaderboard.',
    to: '/timer',
    cta: 'Start studying',
  },
  {
    title: 'Study Plan',
    desc: 'Enter your exam dates and topics. The SM-2 spaced-repetition algorithm schedules daily review cards so you retain everything by exam day.',
    to: '/studyplan',
    cta: 'Build my plan',
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
        <p style={s.heroEyebrow}>NUSMods Helper · AY2026/2027</p>
        <h1 style={s.heroTitle}>Plan smarter.<br />Study better.</h1>
        <p style={s.heroCopy}>
          An all-in-one companion for NUS students — from CourseReg day to final exams.
        </p>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
          <Link to="/timetable">
            <button className="btn-primary" style={{ padding: '9px 22px', fontSize: 14 }}>
              Build my timetable
            </button>
          </Link>
          <CourseRegCountdown />
        </div>
      </div>

      {/* Feature cards */}
      <div style={s.featureGrid}>
        {FEATURES.map(f => (
          <div key={f.title} className="card" style={s.featureCard}>
            <h2 style={s.featureTitle}>{f.title}</h2>
            <p style={s.featureDesc}>{f.desc}</p>
            <Link to={f.to} style={{ marginTop: 'auto' }}>
              <button className="btn-ghost" style={{ width: '100%' }}>{f.cta} →</button>
            </Link>
          </div>
        ))}
      </div>

      {/* CourseReg schedule */}
      <div style={s.section}>
        <h2 style={s.sectionTitle}>AY2026/2027 CourseReg Schedule</h2>
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

        <p style={s.tip}>
          In Round 1A/1B, vacancies are allocated by priority. Having a backup slot ready increases your chance of getting a good timetable.
        </p>
      </div>
    </div>
  )
}

const s = {
  hero: {
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    padding: '40px 36px',
    marginBottom: 24,
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
    alignItems: 'flex-start',
  },
  heroEyebrow: { fontSize: 11, fontWeight: 600, color: 'var(--text-subtle)', letterSpacing: '0.08em', textTransform: 'uppercase', margin: 0 },
  heroTitle: { fontSize: 34, fontWeight: 800, lineHeight: 1.2, margin: 0, letterSpacing: '-0.5px', color: 'var(--text)' },
  heroCopy: { fontSize: 15, color: 'var(--text-muted)', maxWidth: 440, margin: 0, lineHeight: 1.65 },
  featureGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16, marginBottom: 24 },
  featureCard: { display: 'flex', flexDirection: 'column', gap: 10 },
  featureTitle: { fontWeight: 700, fontSize: 15, color: 'var(--text)' },
  featureDesc: { color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.6, flex: 1 },
  section: { background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '28px 28px 20px' },
  sectionTitle: { fontWeight: 700, fontSize: 17, marginBottom: 6, color: 'var(--text)' },
  sectionSub: { color: 'var(--text-muted)', fontSize: 13, marginBottom: 20 },
  semGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 28 },
  semLabel: { fontWeight: 600, fontSize: 13, marginBottom: 8, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' },
  tip: {
    marginTop: 16,
    color: 'var(--text-muted)',
    fontSize: 13,
    paddingTop: 12,
    borderTop: '1px solid var(--border)',
  },
}

const cd = {
  wrap: {
    display: 'flex', flexDirection: 'column', gap: 1,
    padding: '7px 14px', borderRadius: 'var(--radius)',
    border: '1px solid var(--border)', background: 'var(--border-light)',
  },
  label: { fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' },
  val: { fontSize: 14, fontWeight: 700, color: 'var(--text)' },
}

const tbl = {
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 12 },
  th: {
    textAlign: 'left',
    padding: '6px 8px',
    color: 'var(--text-muted)',
    fontWeight: 600,
    fontSize: 11,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    borderBottom: '1px solid var(--border)',
  },
  tr: { borderBottom: '1px solid var(--border-light)' },
  roundCell: { padding: '8px 8px', fontWeight: 600, color: 'var(--primary)', whiteSpace: 'nowrap' },
  dateCell: { padding: '8px 8px', color: 'var(--text)', whiteSpace: 'nowrap' },
  whoCell: { padding: '8px 8px', color: 'var(--text-muted)' },
}
