import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Header from '../components/Header'
import TargetCard from '../components/TargetCard'
import { fetchTargets } from '../services/api'
import './Dashboard.css'

export default function Dashboard() {
  const navigate = useNavigate()
  const [targets, setTargets] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function loadTargets() {
      try {
        const data = await fetchTargets()
        setTargets(data)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    loadTargets()
  }, [])

  return (
    <div className="dashboard-page animate-fade-in">
      <Header 
        title="Fitness OptiMax" 
        subtitle="Progressive Overload Targets" 
      />

      <main className="dashboard-main">
        {/* Log Workout CTA — always at the top */}
        <div className="dashboard-top-bar">
          <div className="dashboard-top-bar-info">
            <span className="dashboard-top-bar-label">Your Training Targets</span>
            <span className="dashboard-top-bar-count">{!loading && !error ? `${targets.length} exercise groups` : ''}</span>
          </div>
          <button
            id="log-workout-btn"
            className="log-workout-btn"
            onClick={() => navigate('/log')}
            title="Record a new workout"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            Record Workout
          </button>
        </div>

        {loading && (
          <div className="target-grid">
            {[1, 2, 3, 4, 5, 6].map(i => (
              <div key={i} className="skeleton skeleton-card"></div>
            ))}
          </div>
        )}

        {error && (
          <div className="error-state">
            <h3>Failed to load targets</h3>
            <p>{error}</p>
          </div>
        )}

        {!loading && !error && (
          <>
            {targets.length === 0 ? (
              <div className="empty-state animate-fade-in">
                <div className="empty-state-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M6 18h12"></path><path d="M6 14h12"></path><path d="M6 10h12"></path><path d="M6 6h12"></path>
                    <rect x="2" y="2" width="20" height="20" rx="4"></rect>
                  </svg>
                </div>
                <h2>Awaiting Data</h2>
                <p>No workout targets found. Complete a session to generate insights.</p>
              </div>
            ) : (
              <div className="target-grid">
                {targets.map(target => (
                  <TargetCard key={target.exercise_group} target={target} />
                ))}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}
