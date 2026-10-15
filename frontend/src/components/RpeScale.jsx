import { RPE_SCALE, rpeLevel } from '../data/rpe'
import './RpeScale.css'

// The legend lists the working range one row each; 0–5 is warm-up territory.
const LEGEND_ROWS = [
  ...RPE_SCALE.filter(l => l.value >= 6).reverse(),
  { value: '0–5', label: 'Light', rir: '5+ reps left', guidance: 'Warm-up / technique', covers: [0, 1, 2, 3, 4, 5] },
]

/**
 * The 0–10 RPE scale. With `onChange` it is a picker (Log Workout); without,
 * a legend that highlights `value` (e.g. the 3-session average).
 */
export default function RpeScale({ value, onChange }) {
  const current = rpeLevel(value === '' || value === null || value === undefined ? undefined : Number(value))

  if (typeof onChange === 'function') {
    return (
      <div className="rpe-picker">
        <div className="rpe-buttons" role="radiogroup" aria-label="RPE, 0 to 10">
          {RPE_SCALE.map(level => {
            const active = current?.value === level.value
            return (
              <button
                key={level.value}
                type="button"
                role="radio"
                aria-checked={active}
                aria-label={`RPE ${level.value}: ${level.label}, ${level.rir}`}
                className={`rpe-btn ${level.value >= 6 ? 'is-working' : ''} ${active ? 'is-active' : ''}`}
                onClick={() => onChange(String(level.value))}
              >
                {level.value}
              </button>
            )
          })}
        </div>
        <div className="rpe-ends" aria-hidden="true">
          <span>Rest</span>
          <span>Max effort</span>
        </div>
        <p className="rpe-selected" aria-live="polite">
          {current
            ? <><strong>RPE {current.value} · {current.label}</strong> · {current.rir}</>
            : 'Pick your effort on the top set: 10 = nothing left, 9 = one more rep, 8 = two more…'}
        </p>
      </div>
    )
  }

  return (
    <div className="rpe-scale" aria-label="RPE scale">
      {LEGEND_ROWS.map(level => {
        const active = current && (level.covers ? level.covers.includes(current.value) : current.value === level.value)
        return (
          <div key={level.value} className={`rpe-row ${active ? 'is-active' : ''}`}>
            <span className="rpe-value">{level.value}</span>
            <span className="rpe-text">
              <span className="rpe-label">{level.label}</span>
              <span className="rpe-rir">{level.rir}</span>
            </span>
            <span className="rpe-guidance">{level.guidance}</span>
          </div>
        )
      })}
    </div>
  )
}
