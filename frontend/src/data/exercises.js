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
