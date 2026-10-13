/**
 * Exercise catalogue for the Log Workout form.
 *
 * The data lives in exercises.json so the monthly programme sync
 * (scripts/sync_exercises.py) can add exercises without touching code.
 * Programme spellings that differ from catalogue names ("SA Row" →
 * "Single Arm Row", etc.) are kept in its `aliases` map.
 */
import catalogue from './exercises.json'

export const EXERCISE_CATEGORIES = catalogue.categories

/** The club's tested 1RM lifts ("Current 1RM" boxes on the programme sheet). */
export const ONE_RM_LIFTS = catalogue.one_rm_lifts || []

/**
 * Which lift's 1RM an exercise's percentage is taken from, e.g.
 * "Snatch High Pull" → "Snatch". Exercises not mapped use their own 1RM.
 */
export function baseLiftFor(exercise) {
  return (catalogue.one_rm_base || {})[exercise] || exercise
}

/** Working-percentage choices offered on Log Workout (50% … 110%). */
export const PERCENT_OPTIONS = Array.from({ length: 13 }, (_, i) => 50 + i * 5)

/** kg for a % of a 1RM, rounded to the nearest 0.5 kg (smallest plate pair). */
export function weightAtPercent(oneRm, percent) {
  return Math.round((oneRm * percent) / 100 * 2) / 2
}

/** % of 1RM makes no sense for the broad "General" groups (Cardio, Core, …). */
const GENERAL = new Set((catalogue.categories.find(c => c.label === 'General') || { exercises: [] }).exercises)
export function usesOneRm(exercise) {
  return !GENERAL.has(exercise)
}
