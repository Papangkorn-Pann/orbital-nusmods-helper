import { NavLink } from 'react-router-dom'

const links = [
  { to: '/',           label: 'Home' },
  { to: '/timetable',  label: 'Timetable' },
  { to: '/analysis',   label: 'Module Analysis' },
  { to: '/timer',      label: 'Study Timer' },
  { to: '/studyplan',  label: 'Study Plan' },
]

export default function Navbar() {
  return (
    <nav style={styles.nav}>
      <div style={styles.inner}>
        <span style={styles.brand}>NUSMods <span style={styles.accent}>Helper</span></span>
        <div style={styles.links}>
          {links.map(l => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === '/'}
              style={({ isActive }) => ({
                ...styles.link,
                ...(isActive ? styles.linkActive : {}),
              })}
            >
              {l.label}
            </NavLink>
          ))}
        </div>
        <span style={styles.year}>AY2025/2026</span>
      </div>
    </nav>
  )
}

const styles = {
  nav: {
    background: '#1e293b',
    position: 'sticky',
    top: 0,
    zIndex: 100,
    boxShadow: '0 1px 4px rgba(0,0,0,.3)',
  },
  inner: {
    maxWidth: 1280,
    margin: '0 auto',
    padding: '0 20px',
    height: 56,
    display: 'flex',
    alignItems: 'center',
    gap: 32,
  },
  brand: { color: 'white', fontWeight: 700, fontSize: 18, whiteSpace: 'nowrap' },
  accent: { color: '#60a5fa' },
  links: { display: 'flex', gap: 4, flex: 1 },
  link: {
    color: '#94a3b8',
    padding: '6px 12px',
    borderRadius: 6,
    fontWeight: 500,
    transition: 'color .15s, background .15s',
  },
  linkActive: { color: 'white', background: 'rgba(255,255,255,.1)' },
  year: { color: '#475569', fontSize: 12, whiteSpace: 'nowrap' },
}
