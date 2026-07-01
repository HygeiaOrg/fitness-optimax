import { useEffect, useState } from 'react'
import Header from '../components/Header'
import TargetCard from '../components/TargetCard'
import { fetchTargets } from '../services/api'
import './Dashboard.css'

export default function Dashboard() {
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
              <div className="empty-state">
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
