import { useState, useEffect, useMemo } from 'react'
import { getUserId } from '../App.jsx'
import {
  getTimetable, updateSlot, removeModule,
  generateTimetable, shareTimetable, exportTimetableIcal,
} from '../api.js'
import ModulePanel from '../components/timetable/ModulePanel.jsx'
import TimetableGrid from '../components/timetable/TimetableGrid.jsx'

const PALETTE = [
  '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6',
  '#ef4444', '#06b6d4', '#f97316', '#6366f1',
  '#14b8a6', '#ec4899', '#84cc16', '#a78bfa',
]

// ── Preference slider ─────────────────────────────────────────────────────────

function PrefSlider({ label, value, onChange }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
      <span style={{ width: 130, fontSize: 13, fontWeight: 500, flexShrink: 0 }}>{label}</span>
      <input
        type="range" min={0} max={1} step={0.05}
        value={value}
        onChange={e => onChange(parseFloat(e.target.value))}
        style={{ flex: 1, width: 'auto' }}
      />
      <span style={{ width: 36, fontSize: 12, textAlign: 'right', color: '#64748b', flexShrink: 0 }}>
        {Math.round(value * 100)}%
      </span>
    </div>
  )
}

// ── Generate modal ────────────────────────────────────────────────────────────

function GenerateModal({ sem, moduleCodes, prefs, setPrefs, generating, genResults, onGenerate, onApply, onClose }) {
  return (
    <div style={ms.overlay} onClick={onClose}>
      <div style={ms.box} onClick={e => e.stopPropagation()}>
        <div style={ms.header}>
          <h3 style={ms.title}>Auto-Generate Timetable</h3>
          <button style={ms.closeBtn} onClick={onClose}>✕</button>
        </div>
        <p style={ms.sub}>
          Finding best Sem {sem} timetables for:{' '}
          <strong>{moduleCodes.join(', ')}</strong>
        </p>

        <div style={{ marginBottom: 16 }}>
          <p style={ms.secTitle}>Preference weights</p>
          <PrefSlider label="Latest Start"  value={prefs.latest_start}  onChange={v => setPrefs(p => ({ ...p, latest_start:  v }))} />
          <PrefSlider label="Earliest End"  value={prefs.earliest_end}  onChange={v => setPrefs(p => ({ ...p, earliest_end:  v }))} />
          <PrefSlider label="Lunch Break"   value={prefs.lunch_break}   onChange={v => setPrefs(p => ({ ...p, lunch_break:   v }))} />
          <PrefSlider label="Compact Days"  value={prefs.compact_days}  onChange={v => setPrefs(p => ({ ...p, compact_days:  v }))} />
          <PrefSlider label="Minimal Gaps"     value={prefs.minimal_gaps}     onChange={v => setPrefs(p => ({ ...p, minimal_gaps:     v }))} />
          <PrefSlider label="Minimize Travel"  value={prefs.minimize_travel}  onChange={v => setPrefs(p => ({ ...p, minimize_travel: v }))} />
        </div>

        {/* Day preference */}
        <div style={{ marginBottom: 16 }}>
          <p style={ms.secTitle}>Preferred days (optional)</p>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 10 }}>
            {['Monday','Tuesday','Wednesday','Thursday','Friday'].map(day => {
              const checked = (prefs.preferred_days || []).includes(day)
              return (
                <label
                  key={day}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 5,
                    cursor: 'pointer', fontSize: 13,
                    padding: '4px 10px', borderRadius: 5,
                    border: `1px solid ${checked ? '#2563eb' : 'var(--border)'}`,
                    background: checked ? '#eff6ff' : 'transparent',
                    color: checked ? '#2563eb' : 'var(--text-muted)',
                    userSelect: 'none',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={e => {
                      setPrefs(p => {
                        const prev = p.preferred_days || []
                        const next = e.target.checked
                          ? [...prev, day]
                          : prev.filter(d => d !== day)
                        return {
                          ...p,
                          preferred_days: next,
                          day_preference: next.length > 0
                            ? (p.day_preference > 0 ? p.day_preference : 0.3)
                            : 0.0,
                        }
                      })
                    }}
                    style={{ width: 'auto', cursor: 'pointer', marginRight: 2 }}
                  />
                  {day.slice(0, 3)}
                </label>
              )
            })}
          </div>
          {(prefs.preferred_days || []).length > 0 && (
            <PrefSlider
              label="Day Pref Weight"
              value={prefs.day_preference || 0.0}
              onChange={v => setPrefs(p => ({ ...p, day_preference: v }))}
            />
          )}
        </div>

        <button
          className="btn-primary"
          onClick={onGenerate}
          disabled={generating}
          style={{ width: '100%', marginBottom: 16 }}
        >
          {generating ? 'Searching… (up to 8 s)' : 'Find Top 5 Timetables'}
        </button>

        {genResults !== null && (
          <div>
            <p style={ms.secTitle}>Results</p>
            {genResults.length === 0 ? (
              <p style={{ color: '#94a3b8', textAlign: 'center', padding: '20px 0', fontSize: 13 }}>
                No conflict-free timetable found. Try removing a module or check that all modules run in Sem {sem}.
              </p>
            ) : (
              genResults.map((r, i) => (
                <div key={i} style={ms.resultRow}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={ms.rank}>#{i + 1}</span>
                    <span style={ms.score}>Score {(r.score * 100).toFixed(0)}%</span>
                    <span style={ms.stars}>
                      {'★'.repeat(Math.round(r.score * 5))}
                      {'☆'.repeat(5 - Math.round(r.score * 5))}
                    </span>
                  </div>
                  <button
                    className="btn-primary"
                    onClick={() => onApply(r)}
                    style={{ padding: '5px 16px', fontSize: 13 }}
                  >
                    Apply
                  </button>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// ── Share modal ───────────────────────────────────────────────────────────────

function ShareModal({ moduleCodes, selected, setSelected, shareLink, sharing, copied, onShare, onCopy, onClose }) {
  return (
    <div style={ms.overlay} onClick={onClose}>
      <div style={ms.box} onClick={e => e.stopPropagation()}>
        <div style={ms.header}>
          <h3 style={ms.title}>Share Timetable</h3>
          <button style={ms.closeBtn} onClick={onClose}>✕</button>
        </div>
        <p style={ms.sub}>Choose which modules to include in the shared link:</p>

        <div style={{ marginBottom: 16 }}>
          {moduleCodes.map(code => (
            <label key={code} style={ms.checkRow}>
              <input
                type="checkbox"
                checked={selected.has(code)}
                onChange={e => {
                  setSelected(prev => {
                    const next = new Set(prev)
                    if (e.target.checked) next.add(code)
                    else next.delete(code)
                    return next
                  })
                }}
                style={{ width: 'auto', marginRight: 10, cursor: 'pointer' }}
              />
              <span style={{ fontWeight: 700, color: '#2563eb', fontSize: 14 }}>{code}</span>
            </label>
          ))}
        </div>

        {!shareLink ? (
          <button
            className="btn-primary"
            onClick={onShare}
            disabled={sharing || selected.size === 0}
            style={{ width: '100%' }}
          >
            {sharing ? 'Creating link…' : 'Create Shareable Link'}
          </button>
        ) : (
          <>
            <p style={{ ...ms.secTitle, marginBottom: 8 }}>Share link</p>
            <div style={ms.linkBox}>
              <input value={shareLink} readOnly style={{ flex: 1, fontSize: 12 }} />
              <button
                className="btn-primary"
                onClick={onCopy}
                style={{ whiteSpace: 'nowrap', flexShrink: 0 }}
              >
                {copied ? '✓ Copied!' : 'Copy'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function Timetable() {
  const userId = getUserId()
  const [sem,           setSem]           = useState(2)
  const [selections,    setSelections]    = useState({})
  const [renderedSlots, setRenderedSlots] = useState([])
  const [saving,        setSaving]        = useState(false)

  // generate modal state
  const [showGenModal, setShowGenModal] = useState(false)
  const [prefs,        setPrefs]        = useState({
    latest_start: 0.2, earliest_end: 0.2, lunch_break: 0.2,
    compact_days: 0.2, minimal_gaps: 0.2, minimize_travel: 0.0,
    day_preference: 0.0, preferred_days: [],
  })
  const [generating,  setGenerating]  = useState(false)
  const [genResults,  setGenResults]  = useState(null)

  // share modal state
  const [showShareModal, setShowShareModal] = useState(false)
  const [shareSelected,  setShareSelected]  = useState(new Set())
  const [shareLink,      setShareLink]      = useState('')
  const [sharing,        setSharing]        = useState(false)
  const [copied,         setCopied]         = useState(false)

  const moduleCodes = Object.keys(selections)

  // Detect manually-selected conflicting slots
  const conflicts = useMemo(() => {
    function toMins(t) { return parseInt(t.slice(0, 2)) * 60 + parseInt(t.slice(2, 4)) }
    const byDay = {}
    for (const slot of renderedSlots) {
      if (!byDay[slot.day]) byDay[slot.day] = []
      byDay[slot.day].push(slot)
    }
    const bad = new Set()
    for (const slots of Object.values(byDay)) {
      for (let i = 0; i < slots.length; i++) {
        for (let j = i + 1; j < slots.length; j++) {
          const [a, b] = [slots[i], slots[j]]
          if (toMins(a.startTime) < toMins(b.endTime) && toMins(b.startTime) < toMins(a.endTime)) {
            bad.add(a.moduleCode); bad.add(b.moduleCode)
          }
        }
      }
    }
    return [...bad]
  }, [renderedSlots])
  const moduleColors = Object.fromEntries(
    moduleCodes.map((c, i) => [c, PALETTE[i % PALETTE.length]])
  )

  // Load saved timetable on mount / sem change
  useEffect(() => {
    getTimetable(userId, sem).then(data => {
      const sel = {}
      for (const s of data.selections) {
        sel[s.module_code] = sel[s.module_code] || {}
        sel[s.module_code][s.lesson_type] = s.class_no
      }
      setSelections(sel)
      setRenderedSlots(data.rendered_slots || [])
    }).catch(() => {})
  }, [sem])

  // ── existing handlers ────────────────────────────────────────────────────────

  async function handleSlotChange(code, lessonType, classNo) {
    setSelections(prev => ({
      ...prev,
      [code]: { ...(prev[code] || {}), [lessonType]: classNo },
    }))
    setSaving(true)
    try {
      await updateSlot(userId, { module_code: code, lesson_type: lessonType, class_no: classNo, sem })
      const data = await getTimetable(userId, sem)
      setRenderedSlots(data.rendered_slots || [])
    } finally {
      setSaving(false)
    }
  }

  async function handleRemoveModule(code) {
    setSelections(prev => {
      const next = { ...prev }
      delete next[code]
      return next
    })
    await removeModule(userId, code, sem)
    const data = await getTimetable(userId, sem)
    setRenderedSlots(data.rendered_slots || [])
  }

  // ── generate handlers ────────────────────────────────────────────────────────

  async function handleGenerate() {
    setGenerating(true)
    setGenResults(null)
    try {
      const data = await generateTimetable({
        module_codes: moduleCodes,
        sem,
        preferences: prefs,
        top_n: 5,
      })
      setGenResults(data.timetables)
    } catch {
      setGenResults([])
    } finally {
      setGenerating(false)
    }
  }

  async function applyGenerated(result) {
    const newSel = {}
    for (const s of result.selections) {
      newSel[s.module_code] = newSel[s.module_code] || {}
      newSel[s.module_code][s.lesson_type] = s.class_no
    }
    setSelections(newSel)
    setRenderedSlots(result.rendered_slots)
    setShowGenModal(false)
    setGenResults(null)

    // Persist: clear old selections then write new ones
    setSaving(true)
    try {
      await Promise.all(moduleCodes.map(c => removeModule(userId, c, sem)))
      await Promise.all(
        result.selections.map(s =>
          updateSlot(userId, {
            module_code: s.module_code,
            lesson_type: s.lesson_type,
            class_no:    s.class_no,
            sem,
          })
        )
      )
    } finally {
      setSaving(false)
    }
  }

  // ── share handlers ────────────────────────────────────────────────────────────

  function openShareModal() {
    setShareSelected(new Set(moduleCodes))
    setShareLink('')
    setCopied(false)
    setShowShareModal(true)
  }

  async function handleShare() {
    setSharing(true)
    try {
      const data = await shareTimetable({
        user_id:      userId,
        sem,
        module_codes: [...shareSelected],
      })
      setShareLink(`${window.location.origin}${data.url}`)
    } catch {
      /* silently fail */
    } finally {
      setSharing(false)
    }
  }

  function copyLink() {
    navigator.clipboard.writeText(shareLink).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2500)
    })
  }

  // ── render ────────────────────────────────────────────────────────────────────

  return (
    <div className="page">
      {/* Modals */}
      {showGenModal && (
        <GenerateModal
          sem={sem}
          moduleCodes={moduleCodes}
          prefs={prefs}
          setPrefs={setPrefs}
          generating={generating}
          genResults={genResults}
          onGenerate={handleGenerate}
          onApply={applyGenerated}
          onClose={() => { setShowGenModal(false); setGenResults(null) }}
        />
      )}
      {showShareModal && (
        <ShareModal
          moduleCodes={moduleCodes}
          selected={shareSelected}
          setSelected={setShareSelected}
          shareLink={shareLink}
          sharing={sharing}
          copied={copied}
          onShare={handleShare}
          onCopy={copyLink}
          onClose={() => setShowShareModal(false)}
        />
      )}

      <div className="no-print" style={styles.topBar}>
        <h1 className="page-title" style={{ marginBottom: 0 }}>Timetable Builder</h1>
        <div style={styles.semSwitch}>
          {[1, 2].map(s => (
            <button
              key={s}
              onClick={() => setSem(s)}
              className={sem === s ? 'btn-primary' : 'btn-ghost'}
              style={{ padding: '6px 18px' }}
            >
              Sem {s}
            </button>
          ))}
        </div>
        {moduleCodes.length > 0 && (
          <>
            <button
              className="btn-ghost"
              onClick={() => { setGenResults(null); setShowGenModal(true) }}
              style={{ padding: '6px 14px' }}
            >
              Generate
            </button>
            <button
              className="btn-ghost"
              onClick={openShareModal}
              style={{ padding: '6px 14px' }}
            >
              Share
            </button>
          </>
        )}
        {moduleCodes.length > 0 && (
          <>
            <button
              className="btn-ghost no-print"
              onClick={() => exportTimetableIcal(userId, sem)}
              style={{ padding: '6px 14px' }}
            >
              Export .ics
            </button>
            <button
              className="btn-ghost no-print"
              onClick={() => window.print()}
              style={{ padding: '6px 14px' }}
            >
              Print
            </button>
          </>
        )}
        {saving && <span style={styles.saving}>Saving…</span>}
      </div>

      <div style={styles.layout}>
        <div className="no-print" style={styles.panelCol}>
          <ModulePanel
            sem={sem}
            selections={selections}
            onSlotChange={handleSlotChange}
            onRemoveModule={handleRemoveModule}
            moduleColors={moduleColors}
          />
        </div>
        <div className="print-area" style={styles.gridCol}>
          {conflicts.length > 0 && (
            <div className="no-print" style={styles.conflictBanner}>
              Time conflict: {conflicts.join(', ')} — pick different slots to resolve.
            </div>
          )}
          <TimetableGrid
            renderedSlots={renderedSlots}
            moduleColors={moduleColors}
          />
          {moduleCodes.length === 0 && (
            <p style={styles.hint}>Add modules from the left panel to see them here.</p>
          )}
          {/* colour legend — hidden on screen, shown when printing */}
          <div className="print-legend">
            {moduleCodes.map(code => (
              <div key={code} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                <div style={{ width: 12, height: 12, borderRadius: 3, background: moduleColors[code], flexShrink: 0 }} />
                <span style={{ fontSize: 12, fontWeight: 700 }}>{code}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Styles ────────────────────────────────────────────────────────────────────

const styles = {
  topBar: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    marginBottom: 20,
    flexWrap: 'wrap',
  },
  semSwitch: { display: 'flex', gap: 6 },
  saving: { color: '#94a3b8', fontSize: 13 },
  layout: {
    display: 'grid',
    gridTemplateColumns: '300px 1fr',
    gap: 20,
    alignItems: 'start',
  },
  panelCol: {
    position: 'sticky',
    top: 72,
    maxHeight: 'calc(100vh - 90px)',
    overflowY: 'auto',
  },
  gridCol: {},
  hint: { color: '#94a3b8', textAlign: 'center', marginTop: 40, fontSize: 14 },
  conflictBanner: {
    background: '#fff1f1', border: '1px solid #fecaca',
    borderRadius: 'var(--radius)', padding: '9px 14px',
    color: '#b91c1c', fontSize: 12, fontWeight: 500,
    marginBottom: 12,
  },
}

const ms = {
  overlay: {
    position: 'fixed', inset: 0,
    background: 'rgba(0,0,0,0.4)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    zIndex: 200, padding: 20,
  },
  box: {
    background: 'white', borderRadius: 'var(--radius)', padding: 24,
    width: '100%', maxWidth: 520,
    maxHeight: '90vh', overflowY: 'auto',
    border: '1px solid var(--border)',
  },
  header: {
    display: 'flex', justifyContent: 'space-between',
    alignItems: 'center', marginBottom: 12,
  },
  title:    { fontWeight: 700, fontSize: 16 },
  closeBtn: {
    background: 'none', border: 'none',
    fontSize: 18, color: 'var(--text-subtle)', cursor: 'pointer',
    padding: '4px 8px', borderRadius: 4,
  },
  sub:      { color: 'var(--text-muted)', fontSize: 13, marginBottom: 16 },
  secTitle: {
    fontWeight: 600, fontSize: 11, color: 'var(--text-subtle)',
    textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 10,
  },
  resultRow: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '10px 0', borderBottom: '1px solid var(--border-light)',
  },
  rank:  { fontWeight: 700, fontSize: 14, color: 'var(--text)' },
  score: { fontSize: 13, color: 'var(--text-muted)' },
  stars: { color: '#d97706', fontSize: 13 },
  checkRow: {
    display: 'flex', alignItems: 'center',
    padding: '9px 0', cursor: 'pointer',
    borderBottom: '1px solid var(--border-light)',
  },
  linkBox: { display: 'flex', gap: 8, alignItems: 'center' },
}
