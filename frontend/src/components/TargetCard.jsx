import { Link } from 'react-router-dom'
import AlertBadge from './AlertBadge.jsx'
import { oneRmLiftsFor } from '../data/exercises'
import './TargetCard.css'

export default function TargetCard({ target, exercise, oneRms = {} }) {
  const {
    exercise_group,
    target_weight_per_rep,
    target_sets,
    target_reps,
    alert_type,
    best_estimated_1rm,
    staleness_alert,
    days_since_last_session
  } = target

  // Optional: Add momentum check here if available in TargetResponse, 
  // or default to alert_type to handle 'GOLDEN_CROSS' logic inside AlertBadge.
  const momentum = null

  // A brand-new exercise group has no history yet, so any of these can be null.
  // Calling .toFixed() on null used to blank the whole page.
  const isNumber = (value) => typeof value === 'number' && Number.isFinite(value)
  const weightPerRep = isNumber(target_weight_per_rep) ? target_weight_per_rep.toFixed(1) : '—'
  const sets = isNumber(target_sets) ? target_sets : '—'
  const totalReps = isNumber(target_reps) ? target_reps : null
  const repsPerSet = isNumber(target_reps) && isNumber(target_sets) && target_sets > 0
    ? Math.round(target_reps / target_sets)
    : '—'

  // Target as a % of the athlete's 1RM: a recorded 1RM for the lift this group
  // is based on, else the best estimate from logged sessions.
  const liftWithMax = oneRmLiftsFor(exercise || exercise_group).find(l => isNumber(oneRms[l]) && oneRms[l] > 0)
  const oneRm = liftWithMax ? oneRms[liftWithMax] : (isNumber(best_estimated_1rm) && best_estimated_1rm > 0 ? best_estimated_1rm : null)
  const percentOfMax = oneRm && isNumber(target_weight_per_rep) ? Math.round((target_weight_per_rep / oneRm) * 100) : null

  return (
    <Link to={`/exercise/${encodeURIComponent(exercise_group)}`} className="target-card">
      <div className="target-card-header">
        <h2 className="target-card-title">{exercise || exercise_group}</h2>
        {percentOfMax !== null && (
          <span
            className="target-card-pct"
            title={liftWithMax ? `Target as a % of your ${liftWithMax} 1RM (${oneRm} kg)` : `Target as a % of your estimated 1RM (${oneRm.toFixed(1)} kg)`}
          >
            {percentOfMax}% {liftWithMax ? '1RM' : 'e1RM'}
          </span>
        )}
      </div>

      <div className="target-card-body">
        <div className="target-card-metric">
          <span className="metric">{weightPerRep}</span>
          <span className="label">kg/rep</span>
        </div>

        <div className="target-card-reps">
          <div className="reps-primary">
            <span className="reps-sets">{sets} sets</span>
            <span className="reps-sep">&times;</span>
            <span className="reps-count">
              {repsPerSet}
              <span className="reps-unit"> reps/set</span>
            </span>
          </div>
          <div className="reps-total">
            {totalReps === null ? 'Awaiting first session' : `${totalReps} total reps`}
          </div>
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
