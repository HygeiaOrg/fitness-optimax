import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import Header from '../components/Header'
import SummaryStats from '../components/SummaryStats'
import SPCChart from '../components/SPCChart'
import GoalToggle from '../components/GoalToggle'
import AlertBadge from '../components/AlertBadge'
import { fetchChartData, fetchTargets } from '../services/api'
import './ExerciseDetail.css'

export default function ExerciseDetail() {
  const { group } = useParams()
  const decodedGroup = decodeURIComponent(group)
  
  const [chartData, setChartData] = useState(null)
  const [targetData, setTargetData] = useState(null)
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

  const handleGoalChange = (newGoal) => {
    if (targetData) {
      setTargetData({ ...targetData, training_goal: newGoal })
    }
  }

  return (
    <div className="exercise-detail-page animate-fade-in">
      <Header 
        title={decodedGroup} 
        backTo="/"
        subtitle={targetData ? `${targetData.target_sets} sets × ${targetData.target_reps} reps` : ''}
      />

      <main className="exercise-detail-main">
        <div className="exercise-header-actions">
          {targetData && (
            <GoalToggle 
              exerciseGroup={decodedGroup} 
              initialGoal={targetData.training_goal}
              onGoalChange={handleGoalChange}
            />
          )}
        </div>

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
                  {targetData.goal_aligned && <span className="insight-aligned">✓ Goal Aligned</span>}
                </div>
                <h3 className="insight-message">{targetData.alert_message}</h3>
                <p className="insight-target">
                  Target: <strong>{targetData.target_weight_per_rep.toFixed(1)} kg</strong> for {targetData.target_sets} × {targetData.target_reps}
                </p>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}
