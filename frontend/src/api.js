const BASE = '/api'

// ── helpers ───────────────────────────────────────────────────────────────────

async function get(path) {
  const r = await fetch(BASE + path)
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

async function post(path, body) {
  const r = await fetch(BASE + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

async function put(path, body) {
  const r = await fetch(BASE + path, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

async function del(path) {
  const r = await fetch(BASE + path, { method: 'DELETE' })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

// ── user management ───────────────────────────────────────────────────────────

export const createUser = (body) => post('/users', body)
export const getUser = (userId) => get(`/users/${userId}`)
export const updateUser = (userId, body) => put(`/users/${userId}`, body)

// ── module search & slots ─────────────────────────────────────────────────────

export const searchModules = (q) => get(`/modules?q=${encodeURIComponent(q)}&limit=10`)
export const getModuleSlots = (code, sem = 1) => get(`/modules/${code}/slots?sem=${sem}`)
export const getCourseInfo = (code) => get(`/course/${code}`)

// ── timetable ─────────────────────────────────────────────────────────────────

export const getTimetable = (userId, sem = 1) => get(`/timetable/${userId}?sem=${sem}`)
export const updateSlot = (userId, body) => put(`/timetable/${userId}/slots`, body)
export const removeModule = (userId, code, sem = 1) =>
  del(`/timetable/${userId}/modules/${code}?sem=${sem}`)

// ── study timer ───────────────────────────────────────────────────────────────

export const startSession = (userId) => post('/timer/sessions', { user_id: userId })
export const stopSession = (sessionId, endTime) =>
  put(`/timer/sessions/${sessionId}`, { end_time: endTime })
export const getTimerStats = (userId) => get(`/timer/stats/${userId}`)
export const getLeaderboard = (faculty) =>
  get(`/timer/leaderboard${faculty ? `?faculty=${encodeURIComponent(faculty)}` : ''}`)

// ── study groups ──────────────────────────────────────────────────────────────

export const createGroup = (groupName, userId) =>
  post('/groups', { group_name: groupName, user_id: userId })
export const joinGroup = (inviteCode, userId) =>
  post(`/groups/${inviteCode}/join`, { user_id: userId })
export const getGroup = (inviteCode) => get(`/groups/${inviteCode}`)

// ── timetable generation & sharing ───────────────────────────────────────────

export const generateTimetable   = (body)  => post('/timetable/generate', body)
export const shareTimetable      = (body)  => post('/timetable/share', body)
export const getSharedTimetable  = (token) => get(`/timetable/shared/${token}`)

// ── study plan ────────────────────────────────────────────────────────────────

export const addExam = (body) => post('/studyplan/exams', body)
export const getTodayCards = (userId) => get(`/studyplan/${userId}/today`)
export const reviewCard = (cardId, quality) =>
  put(`/studyplan/cards/${cardId}/review`, { quality })
export const getSchedule = (userId) => get(`/studyplan/${userId}/schedule`)
export const deleteCard  = (cardId) => del(`/studyplan/cards/${cardId}`)
export const deleteExam  = (userId, moduleCode) =>
  del(`/studyplan/${userId}/exams/${moduleCode}`)

export function exportStudyPlan(userId) {
  const a = document.createElement('a')
  a.href = `${BASE}/studyplan/${userId}/export.ics`
  a.download = 'study-plan.ics'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}
