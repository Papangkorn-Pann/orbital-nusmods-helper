import { Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import Navbar from './components/Navbar.jsx'
import Home from './pages/Home.jsx'
import Timetable from './pages/Timetable.jsx'
import Timer from './pages/Timer.jsx'
import StudyPlan from './pages/StudyPlan.jsx'
import ModuleAnalysis from './pages/ModuleAnalysis.jsx'
import SharedTimetable from './pages/SharedTimetable.jsx'
import Compare from './pages/Compare.jsx'
import CourseReg from './pages/CourseReg.jsx'
import { createUser } from './api.js'

function getUserId() {
  let id = localStorage.getItem('userId')
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem('userId', id)
  }
  return id
}

export default function App() {
  useEffect(() => {
    const id = getUserId()
    // Silently register user on first visit
    createUser({ user_id: id }).catch(() => {})
  }, [])

  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/"               element={<Home />} />
        <Route path="/timetable"      element={<Timetable />} />
        <Route path="/timer"          element={<Timer />} />
        <Route path="/studyplan"      element={<StudyPlan />} />
        <Route path="/analysis"       element={<ModuleAnalysis />} />
        <Route path="/shared/:token"  element={<SharedTimetable />} />
        <Route path="/compare"        element={<Compare />} />
        <Route path="/coursereg"      element={<CourseReg />} />
      </Routes>
    </>
  )
}

export { getUserId }
