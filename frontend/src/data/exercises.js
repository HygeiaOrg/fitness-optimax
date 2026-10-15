/**
 * Exercise catalogue for Log Workout and the dashboard.
 *
 * Strength only: Olympic lifts (Snatch, Clean & Jerk) and their derivatives
 * are logged by name; everything else is logged under the muscle group it was
 * captured under on the original data capture sheet ("Leg, Quads", …).
 *
 * The data lives in exercises.json so the monthly programme sync
 * (scripts/sync_exercises.py) can add exercises without touching code.
 */
import catalogue from './exercises.json'

export const EXERCISE_CATEGORIES = catalogue.categories

/** The one athlete the app tracks for now. */
export const DEFAULT_ATHLETE = 'John Hartley'

/** The club's tested 1RM lifts ("Current 1RM" boxes on the programme sheet). */
export const ONE_RM_LIFTS = catalogue.one_rm_lifts || []

const categoryByName = new Map(
  catalogue.categories.flatMap(c => c.exercises.map(e => [e.toLowerCase(), c]))
)

/** The catalogue category an exercise group belongs to (case-insensitive), or undefined. */
export function categoryFor(exercise) {
  return categoryByName.get(String(exercise).toLowerCase())
}

export function isOlympic(exercise) {
  return categoryFor(exercise)?.kind === 'olympic'
}

/**
 * Which lift's 1RM an exercise's percentage is taken from, e.g.
 * "Snatch High Pull" → "Snatch". Exercises not mapped use their own 1RM.
 */
export function baseLiftFor(exercise) {
  return (catalogue.one_rm_base || {})[exercise] || exercise
}

/**
 * The 1RM lifts that make sense for an exercise group, most relevant first:
 * an Olympic lift's base lift, a muscle group's reference lifts
 * ("Leg, Quads" → Back Squat, Front Squat), otherwise the group itself.
 */
export function oneRmLiftsFor(exercise) {
  const reference = (catalogue.one_rm_reference || {})[exercise]
  if (reference && reference.length) return reference
  return [baseLiftFor(exercise)]
}

/** Working-percentage choices offered on Log Workout (50% … 110%). */
export const PERCENT_OPTIONS = Array.from({ length: 13 }, (_, i) => 50 + i * 5)

/** kg for a % of a 1RM, rounded to the nearest 0.5 kg (smallest plate pair). */
export function weightAtPercent(oneRm, percent) {
  return Math.round((oneRm * percent) / 100 * 2) / 2
}

/** Strength training zones by % of 1RM, heaviest first. */
export const STRENGTH_ZONES = [
  { min: 90, label: 'Max strength', reps: '1–2 reps' },
  { min: 80, label: 'Strength', reps: '2–4 reps' },
  { min: 70, label: 'Strength-speed', reps: '3–5 reps' },
  { min: 60, label: 'Technique', reps: '3–6 reps' },
  { min: 0, label: 'Warm-up', reps: '' },
]

export function zoneFor(percent) {
  return STRENGTH_ZONES.find(z => percent >= z.min)
}
