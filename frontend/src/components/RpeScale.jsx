import { RPE_SCALE, rpeLevel } from '../data/rpe'
import './RpeScale.css'

/**
 * The 1–5 RPE scale. With `onChange` it is a picker (Log Workout); without,
 * a legend that highlights `value` (e.g. the 3-session average).
 */
export default function RpeScale({ value, onChange }) {
  const current = rpeLevel(typeof value === 'string' ? Number(value) : value)
  const interactive = typeof onChange === 'function'

  return (
    <div className={`rpe-scale ${interactive ? 'is-picker' : ''}`} role={interactive ? 'radiogroup' : undefined} aria-label="RPE scale">
      {RPE_SCALE.map(level => {
        const active = current?.value === level.value
        const content = (
          <>
            <span className="rpe-value">{level.value}</span>
            <span className="rpe-text">
              <span className="rpe-label">{level.label}</span>
              <span className="rpe-rir">{level.rir} · RPE {level.rpe10}/10</span>
            </span>
          </>
        )
        return interactive ? (
          <button
            key={level.value}
            type="button"
            role="radio"
            aria-checked={active}
            aria-label={`RPE ${level.value}: ${level.label}, ${level.rir}`}
            className={`rpe-row ${active ? 'is-active' : ''}`}
            onClick={() => onChange(String(level.value))}
          >
            {content}
          </button>
        ) : (
          <div key={level.value} className={`rpe-row ${active ? 'is-active' : ''}`}>
            {content}
            <span className="rpe-guidance">{level.guidance}</span>
          </div>
        )
      })}
    </div>
  )
}
