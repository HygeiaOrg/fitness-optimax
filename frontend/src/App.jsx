import { Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard.jsx'
import ExerciseDetail from './pages/ExerciseDetail.jsx'
import LogWorkout from './pages/LogWorkout.jsx'
import Privacy from './pages/Privacy.jsx'
import OnboardingGate from './components/OnboardingGate.jsx'
import './App.css'

function App() {
  return (
    <div className="app-shell">
      <OnboardingGate>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/exercise/:group" element={<ExerciseDetail />} />
          <Route path="/log" element={<LogWorkout />} />
          <Route path="/privacy" element={<Privacy />} />
        </Routes>
      </OnboardingGate>
    </div>
  )
}

export default App
