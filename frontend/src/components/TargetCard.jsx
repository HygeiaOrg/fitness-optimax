import { Link } from 'react-router-dom'
import AlertBadge from './AlertBadge.jsx'
import './TargetCard.css'

export default function TargetCard({ target }) {
  const {
    exercise_group,
    target_weight_per_rep,
    target_sets,
    target_reps,
    alert_type,
    goal_aligned,
    staleness_alert,
    days_since_last_session
  } = target

  // Optional: Add momentum check here if available in TargetResponse, 
  // or default to alert_type to handle 'GOLDEN_CROSS' logic inside AlertBadge.
  const momentum = null 

  return (
    <Link to={`/exercise/${encodeURIComponent(exercise_group)}`} className="target-card">
      <div className="target-card-header">
        <h2 className="target-card-title">{exercise_group}</h2>
        {goal_aligned && (
          <span className="target-card-aligned" title="Aligned with your training goal">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M13.3333 4L6.00001 11.3333L2.66667 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </span>
        )}
      </div>

      <div className="target-card-body">
        <div className="target-card-metric">
          <span className="metric">{target_weight_per_rep.toFixed(1)}</span>
          <span className="label">kg/rep</span>
        </div>
        
        <div className="target-card-reps">
          {target_sets} sets &times; {target_reps} reps
        </div>
      </div>

      <div className="target-card-footer">
        <AlertBadge alertType={alert_type} momentum={momentum} />
        {staleness_alert && (
          <div className="target-card-stale">
            <span className="stale-dot"></span>
            {days_since_last_session}d ago
          </div>
        )}
      </div>
    </Link>
  )
}
