import { useState } from 'react'
import { Link } from 'react-router-dom'
import RpeScale from './RpeScale'
import { oneRmLiftsFor, weightAtPercent, zoneFor } from '../data/exercises'
import { rpeLevel } from '../data/rpe'
import './StrengthPanel.css'

const TABLE_PERCENTS = [100, 95, 90, 85, 80, 75, 70, 65, 60]
const isNumber = (v) => typeof v === 'number' && Number.isFinite(v) && v > 0

/**
 * Strength context for one exercise group: the athlete's 1RM (recorded, or
 * estimated from logged sessions), working weights at % of 1RM with the
 * strength zone each falls in, and the RPE scale with recent effort marked.
 */
export default function StrengthPanel({ exercise, oneRms, target }) {
  const lifts = oneRmLiftsFor(exercise)
  const [lift, setLift] = useState(() => lifts.find(l => isNumber(oneRms?.[l])) || lifts[0])

  const recorded = oneRms?.[lift]
  const estimated = target?.best_estimated_1rm
  const reference = isNumber(recorded) ? recorded : (isNumber(estimated) ? estimated : null)
  const referenceLabel = isNumber(recorded) ? `${lift} 1RM` : 'estimated 1RM'

  const targetKg = target?.target_weight_per_rep
  const targetPct = reference && isNumber(targetKg) ? Math.round((targetKg / reference) * 100) : null
  const nearestPct = targetPct === null ? null
    : TABLE_PERCENTS.reduce((best, p) => (Math.abs(p - targetPct) < Math.abs(best - targetPct) ? p : best))
  const effort = rpeLevel(target?.rpe_avg_3)

  return (
    <section className="strength-panel" aria-label="One rep max and effort">
      <div className="strength-card">
        <div className="strength-card-head">
          <h3 className="strength-title">One Rep Max</h3>
          {lifts.length > 1 && (
            <div className="strength-lifts" role="tablist" aria-label="1RM lift">
              {lifts.map(l => (
                <button
                  key={l}
                  type="button"
                  role="tab"
                  aria-selected={l === lift}
                  className={`strength-lift ${l === lift ? 'is-active' : ''}`}
                  onClick={() => setLift(l)}
                >
                  {l}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="strength-maxes">
          <div className="strength-max">
            <span className="strength-max-value">{isNumber(recorded) ? `${recorded} kg` : '—'}</span>
            <span className="strength-max-label">
              {lift} 1RM{!isNumber(recorded) && <> · <Link to="/log">add it</Link></>}
            </span>
          </div>
          <div className="strength-max">
            <span className="strength-max-value is-estimate">{isNumber(estimated) ? `${estimated.toFixed(1)} kg` : '—'}</span>
            <span className="strength-max-label">Estimated from your sessions</span>
          </div>
        </div>

        {targetPct !== null && (
          <p className="strength-target">
            Next target <strong>{targetKg.toFixed(1)} kg</strong> ≈ <strong>{targetPct}%</strong> of your {referenceLabel}
            {zoneFor(targetPct) && <span className="strength-zone-chip">{zoneFor(targetPct).label}</span>}
          </p>
        )}

        {reference ? (
          <table className="strength-table">
            <caption>% of {referenceLabel} ({isNumber(recorded) ? recorded : reference.toFixed(1)} kg)</caption>
            <thead>
              <tr><th scope="col">%</th><th scope="col">kg</th><th scope="col">Zone</th></tr>
            </thead>
            <tbody>
              {TABLE_PERCENTS.map(p => {
                const zone = zoneFor(p)
                return (
                  <tr key={p} className={p === nearestPct ? 'is-target' : ''}>
                    <td>{p}%</td>
                    <td className="strength-kg">{weightAtPercent(reference, p)}</td>
                    <td className="strength-zone">{zone.label}{zone.reps && <span> · {zone.reps}</span>}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        ) : (
          <p className="strength-empty">Record a {lift} 1RM to see your working weights at each %.</p>
        )}
      </div>

      <div className="strength-card">
        <div className="strength-card-head">
          <h3 className="strength-title">RPE Scale</h3>
          {effort && (
            <span className="strength-effort">
              Last 3 sessions: <strong>{target.rpe_avg_3.toFixed(1)}</strong> · {effort.label}
            </span>
          )}
        </div>
        <RpeScale value={target?.rpe_avg_3} />
      </div>
    </section>
  )
}
