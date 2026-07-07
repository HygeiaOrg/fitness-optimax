import { Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard.jsx'
import ExerciseDetail from './pages/ExerciseDetail.jsx'
import LogWorkout from './pages/LogWorkout.jsx'
import './App.css'

function App() {
  return (
    <div className="app-shell">
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/exercise/:group" element={<ExerciseDetail />} />
        <Route path="/log" element={<LogWorkout />} />
      </Routes>
    </div>
  )
}

export default App
