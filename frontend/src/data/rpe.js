/**
 * RPE (Rate of Perceived Exertion) on the 0–10 scale, read by reps in reserve
 * (10 = nothing left, 9 = one more rep, …). The original data capture sheet
 * used 1–5; sql/01_stg_workouts.sql maps that history across (5 → 10 … 1 → 6).
 */
export const RPE_SCALE = [
  { value: 0, label: 'Rest', rir: 'No effort', guidance: '' },
  { value: 1, label: 'Very light', rir: 'Barely any effort', guidance: 'Warm-up' },
  { value: 2, label: 'Very light', rir: 'Barely any effort', guidance: 'Warm-up' },
  { value: 3, label: 'Light', rir: 'Many reps left', guidance: 'Warm-up' },
  { value: 4, label: 'Light', rir: 'Many reps left', guidance: 'Warm-up' },
  { value: 5, label: 'Moderate', rir: '5+ reps left', guidance: 'Technique / build-up' },
  { value: 6, label: 'Moderate', rir: '4 reps left', guidance: 'Bar speed fast' },
  { value: 7, label: 'Challenging', rir: '3 reps left', guidance: 'Add load next time' },
  { value: 8, label: 'Hard', rir: '2 reps left', guidance: 'Room for a small increase' },
  { value: 9, label: 'Very hard', rir: '1 rep left', guidance: 'Productive strength work' },
  { value: 10, label: 'Maximal', rir: 'Nothing left', guidance: 'Top single or a missed rep' },
]

/** The scale entry nearest an (averaged) RPE, or undefined. */
export function rpeLevel(value) {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0) return undefined
  const rounded = Math.min(10, Math.round(value))
  return RPE_SCALE.find(r => r.value === rounded)
}
