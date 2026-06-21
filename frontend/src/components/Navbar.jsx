import { useState } from 'react'
import { NavLink } from 'react-router-dom'

const links = [
  { to: '/',           label: 'Home' },
  { to: '/timetable',  label: 'Timetable' },
  { to: '/coursereg',  label: 'CourseReg' },
  { to: '/analysis',   label: 'Module Analysis' },
  { to: '/compare',    label: 'Compare' },
  { to: '/timer',      label: 'Study Timer' },
  { to: '/studyplan',  label: 'Study Plan' },
]

export default function Navbar() {
  const [open, setOpen] = useState(false)

  return (
    <nav style={styles.nav}>
      <div style={styles.inner}>
        <span style={styles.brand}>NUSMods <span style={styles.accent}>Helper</span></span>

        {/* Desktop links */}
        <div className="nav-links">
          {links.map(l => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === '/'}
              style={({ isActive }) => ({ ...styles.link, ...(isActive ? styles.linkActive : {}) })}
            >
              {l.label}
            </NavLink>
          ))}
        </div>

        {/* Mobile hamburger */}
        <button className="nav-burger" onClick={() => setOpen(o => !o)} aria-label="Menu">
          <span style={{ ...styles.bar, transform: open ? 'rotate(45deg) translate(5px, 5px)' : 'none' }} />
          <span style={{ ...styles.bar, opacity: open ? 0 : 1 }} />
          <span style={{ ...styles.bar, transform: open ? 'rotate(-45deg) translate(5px, -5px)' : 'none' }} />
        </button>
      </div>

      {/* Mobile drawer */}
      {open && (
        <div style={styles.drawer}>
          {links.map(l => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === '/'}
              style={({ isActive }) => ({ ...styles.drawerLink, ...(isActive ? styles.drawerLinkActive : {}) })}
              onClick={() => setOpen(false)}
            >
              {l.label}
            </NavLink>
          ))}
        </div>
      )}
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
  link: {
    color: '#94a3b8',
    padding: '5px 11px',
    borderRadius: 5,
    fontWeight: 500,
    fontSize: 14,
    transition: 'color .12s, background .12s',
  },
  linkActive: { color: 'white', background: 'rgba(255,255,255,.1)' },
  bar: {
    display: 'block', width: 22, height: 2,
    background: '#94a3b8', borderRadius: 2,
    transition: 'transform .2s, opacity .2s',
  },
  drawer: {
    background: '#1e293b',
    borderTop: '1px solid rgba(255,255,255,.08)',
    display: 'flex', flexDirection: 'column',
  },
  drawerLink: {
    padding: '14px 24px',
    color: '#94a3b8', fontWeight: 500, fontSize: 15,
    borderBottom: '1px solid rgba(255,255,255,.06)',
    display: 'block',
  },
  drawerLinkActive: { color: 'white', background: 'rgba(255,255,255,.06)' },
}
