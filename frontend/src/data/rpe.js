/**
 * RPE (Rate of Perceived Exertion) on the 1–5 scale used since the original
 * data capture sheet, and by the targets engine (sql/08_workout_targets.sql).
 * `rpe10` is the familiar 1–10 equivalent, by reps left in the tank.
 */
export const RPE_SCALE = [
  { value: 1, label: 'Very easy', rir: '5+ reps left', rpe10: '≤6', guidance: 'Warm-up weight' },
  { value: 2, label: 'Easy', rir: '3–4 reps left', rpe10: '7', guidance: 'Add load next time' },
  { value: 3, label: 'Moderate', rir: '2 reps left', rpe10: '8', guidance: 'Room for a small increase' },
  { value: 4, label: 'Hard', rir: '1 rep left', rpe10: '9', guidance: 'Productive strength work' },
  { value: 5, label: 'Maximal', rir: 'Nothing left', rpe10: '10', guidance: 'Top single or a missed rep' },
]

/** The scale entry nearest an (averaged) RPE, or undefined. */
export function rpeLevel(value) {
  if (typeof value !== 'number' || !Number.isFinite(value) || value <= 0) return undefined
  const rounded = Math.min(5, Math.max(1, Math.round(value)))
  return RPE_SCALE.find(r => r.value === rounded)
}
