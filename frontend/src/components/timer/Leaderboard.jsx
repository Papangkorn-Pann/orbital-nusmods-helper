import { useState, useEffect } from 'react'
import { getLeaderboard, createGroup, joinGroup, getGroup } from '../../api.js'

const FACULTIES = ['', 'SOC', 'FOS', 'FOE', 'BIZ', 'LAW', 'MED', 'DEN', 'FASS', 'CDE', 'YST', 'SPH']

function fmtH(s) { return s ? `${(s / 3600).toFixed(1)}h` : '0.0h' }

export default function Leaderboard({ userId }) {
  const [faculty, setFaculty]       = useState('')
  const [board, setBoard]           = useState([])
  const [groupCode, setGroupCode]   = useState('')
  const [groupName, setGroupName]   = useState('')
  const [myGroup, setMyGroup]       = useState(null)
  const [inviteInput, setInviteInput] = useState('')
  const [msg, setMsg] = useState('')

  function loadBoard(f) {
    getLeaderboard(f).then(setBoard).catch(() => {})
  }

  useEffect(() => { loadBoard(faculty) }, [faculty])

  function handleCreateGroup() {
    if (!groupName.trim()) return
    createGroup(groupName, userId).then(data => {
      setMsg(`Group created! Invite code: ${data.invite_code}`)
      setGroupCode(data.invite_code)
      loadGroup(data.invite_code)
    }).catch(() => setMsg('Failed to create group'))
  }

  function handleJoinGroup() {
    if (!inviteInput.trim()) return
    joinGroup(inviteInput.trim().toUpperCase(), userId).then(() => {
      setGroupCode(inviteInput.trim().toUpperCase())
      loadGroup(inviteInput.trim().toUpperCase())
      setMsg('')
    }).catch(() => setMsg('Group not found'))
  }

  function loadGroup(code) {
    getGroup(code).then(setMyGroup).catch(() => {})
  }

  return (
    <div style={styles.wrapper}>
      {/* global leaderboard */}
      <div className="card">
        <div style={styles.boardHeader}>
          <h3 style={styles.title}>Weekly Leaderboard</h3>
          <select value={faculty} onChange={e => setFaculty(e.target.value)} style={{ width: 120 }}>
            {FACULTIES.map(f => <option key={f} value={f}>{f || 'All'}</option>)}
          </select>
        </div>
        <table style={styles.table}>
          <thead>
            <tr style={styles.th}>
              <td style={{ width: 32 }}>#</td>
              <td>Name</td>
              <td>Faculty</td>
              <td style={{ textAlign: 'right' }}>Hours</td>
            </tr>
          </thead>
          <tbody>
            {board.length === 0 && (
              <tr><td colSpan={4} style={styles.empty}>No data yet — start studying!</td></tr>
            )}
            {board.map((u, i) => (
              <tr key={u.user_id} style={{ ...styles.row, background: u.user_id === userId ? '#eff6ff' : 'transparent' }}>
                <td style={styles.rank}>
                  {i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : i + 1}
                </td>
                <td>{u.display_name}{u.user_id === userId ? ' (you)' : ''}</td>
                <td style={{ color: '#94a3b8' }}>{u.faculty || '—'}</td>
                <td style={{ textAlign: 'right', fontWeight: 700, color: '#2563eb' }}>
                  {fmtH(u.week_seconds)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* study groups */}
      <div className="card">
        <h3 style={styles.title}>Study Groups</h3>

        {!myGroup && (
          <div style={styles.groupActions}>
            <div style={styles.groupRow}>
              <input placeholder="Group name" value={groupName}
                onChange={e => setGroupName(e.target.value)} style={{ flex: 1 }} />
              <button className="btn-primary" onClick={handleCreateGroup}>Create</button>
            </div>
            <div style={styles.groupRow}>
              <input placeholder="Invite code" value={inviteInput}
                onChange={e => setInviteInput(e.target.value.toUpperCase())} style={{ flex: 1 }} />
              <button className="btn-ghost" onClick={handleJoinGroup}>Join</button>
            </div>
            {msg && <p style={styles.msg}>{msg}</p>}
          </div>
        )}

        {myGroup && (
          <div>
            <div style={styles.groupInfo}>
              <span style={styles.groupName}>{myGroup.group_name}</span>
              <span style={styles.invCode}>Code: <b>{myGroup.invite_code}</b></span>
            </div>
            <table style={styles.table}>
              <thead>
                <tr style={styles.th}><td>#</td><td>Member</td><td style={{ textAlign: 'right' }}>Hours this week</td></tr>
              </thead>
              <tbody>
                {(myGroup.leaderboard || []).map((u, i) => (
                  <tr key={u.user_id} style={{ ...styles.row, background: u.user_id === userId ? '#eff6ff' : 'transparent' }}>
                    <td style={styles.rank}>{i + 1}</td>
                    <td>{u.display_name}{u.user_id === userId ? ' (you)' : ''}</td>
                    <td style={{ textAlign: 'right', fontWeight: 700, color: '#2563eb' }}>{fmtH(u.week_seconds)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

const styles = {
  wrapper: { display: 'flex', flexDirection: 'column', gap: 20 },
  boardHeader: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 },
  title: { fontWeight: 700, fontSize: 16, marginBottom: 12 },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 13 },
  th: { color: '#94a3b8', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', borderBottom: '1px solid #e2e8f0' },
  row: { borderBottom: '1px solid #f1f5f9' },
  rank: { fontSize: 16, padding: '6px 0' },
  empty: { textAlign: 'center', color: '#94a3b8', padding: 20 },
  groupActions: { display: 'flex', flexDirection: 'column', gap: 10 },
  groupRow: { display: 'flex', gap: 8 },
  msg: { color: '#2563eb', fontSize: 13, fontWeight: 600 },
  groupInfo: { display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 },
  groupName: { fontWeight: 700, fontSize: 15 },
  invCode: { fontSize: 13, color: '#64748b' },
}
