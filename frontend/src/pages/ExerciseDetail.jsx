import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Header from '../components/Header'
import SummaryStats from '../components/SummaryStats'
import SPCChart from '../components/SPCChart'
import AlertBadge from '../components/AlertBadge'
import StrengthPanel from '../components/StrengthPanel'
import { fetchChartData, fetchOneRepMaxes, fetchTargets } from '../services/api'
import { DEFAULT_ATHLETE, categoryFor } from '../data/exercises'
import './ExerciseDetail.css'

export default function ExerciseDetail() {
  const { group } = useParams()
  const navigate = useNavigate()
  const decodedGroup = decodeURIComponent(group)
  
  const [chartData, setChartData] = useState(null)
  const [targetData, setTargetData] = useState(null)
  const [oneRms, setOneRms] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true)
        // Fetch chart data and the specific target data concurrently
        const [chartRes, targetsRes] = await Promise.all([
          fetchChartData(decodedGroup),
          fetchTargets()
        ])
        
        setChartData(chartRes)
        const specificTarget = targetsRes.find(t => t.exercise_group === decodedGroup)
        setTargetData(specificTarget)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [decodedGroup])

  // 1RMs are context, not essential: the page still works without them.
  useEffect(() => {
    let cancelled = false
    fetchOneRepMaxes(DEFAULT_ATHLETE)
      .then(map => { if (!cancelled) setOneRms(map) })
      .catch(() => {})
    return () => { cancelled = true }
  }, [])

  const category = categoryFor(decodedGroup)
  // BigQuery hands the group back INITCAP'd; use the catalogue's spelling for 1RM lookups.
  const exerciseName = category?.exercises.find(e => e.toLowerCase() === decodedGroup.toLowerCase()) || decodedGroup

  return (
    <div className="exercise-detail-page animate-fade-in">
      <Header 
        title={decodedGroup} 
        backTo="/"
        subtitle={category ? category.label : ''}
      />

      <main className="exercise-detail-main">

        {loading && (
          <div className="detail-loading">
            <div className="skeleton skeleton-metric" style={{ width: '100%', height: '80px' }}></div>
            <div className="skeleton skeleton-card" style={{ height: '400px' }}></div>
          </div>
        )}

        {error && (
          <div className="error-state">
            <h3>Failed to load exercise data</h3>
            <p>{error}</p>
          </div>
        )}

        {!loading && !error && chartData && (
          <>
            {chartData.sessions.length === 0 ? (
              <div className="empty-state animate-fade-in" style={{ marginTop: 'var(--space-2xl)' }}>
                <div className="empty-state-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line>
                  </svg>
                </div>
                <h2>No Session History</h2>
                <p>We don't have enough data to chart your performance yet. Log your first session to begin tracking.</p>
                <button className="primary-button cta-button" onClick={() => navigate('/log')}>
                  Log First Workout
                </button>
              </div>
            ) : (
              <>
                <SummaryStats 
                  stats={{
                    rollingAvg: targetData?.rolling_avg_5 || null,
                    rpeAvg: targetData?.rpe_avg_3 || null,
                    totalSessions: chartData.sessions.length
                  }} 
                />

                <SPCChart data={chartData} />

                {targetData && (
                  <div className="exercise-insight-card">
                    <div className="insight-header">
                      <AlertBadge alertType={targetData.alert_type} />
                    </div>
                    <h3 className="insight-message">{targetData.alert_message}</h3>
                    {typeof targetData.target_weight_per_rep === 'number' && (
                      <p className="insight-target">
                        Target: <strong>{targetData.target_weight_per_rep.toFixed(1)} kg</strong> {targetData.target_sets > 0 && targetData.target_reps > 0 && (
                          <> for {targetData.target_sets} sets × {Math.round(targetData.target_reps / targetData.target_sets)} reps</>
                        )}
                      </p>
                    )}
                  </div>
                )}

                <StrengthPanel key={exerciseName} exercise={exerciseName} oneRms={oneRms} target={targetData} />
              </>
            )}
          </>
        )}
      </main>
    </div>
  )
}
