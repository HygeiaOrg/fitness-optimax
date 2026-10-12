/**
 * Exercise catalogue for the Log Workout form.
 *
 * Source: North Tyneside Barbells — Olympic Lifting Programme, September 2026
 * (Wk1–Wk5). Names are normalised so they survive stg_workouts' INITCAP()
 * unchanged (no all-caps abbreviations like "SA" or "RDL") and contain no "/",
 * which would break the /api/charts/{exercise_group} route.
 *
 * Programme name → catalogue name, where they differ:
 *   "SA Row"                    → "Single Arm Row"
 *   "SL RDL"                    → "Single Leg Romanian Deadlift"
 *   "Back Ext"                  → "Back Extension"
 *   "Back Ext ISO Holds"        → "Back Extension Iso Hold"
 *   "Ab Roll outs"              → "Ab Rollout"
 *   "Hanging / Lying Leg Raise" → "Leg Raise"
 *   "Lat Pull Down"             → "Lat Pulldown"
 *   "Split Squats"              → "Split Squat"
 *   "Deadbugs"                  → "Dead Bug"
 *   "Cable Curls"               → "Cable Curl"
 *   "Side Bends"                → "Side Bend"
 */
export const EXERCISE_CATEGORIES = [
  {
    label: 'Olympic Lifts',
    exercises: [
      'Snatch',
      'Power Snatch',
      'Hang Snatch',
      'Clean & Jerk',
      'Power Clean & Power Jerk',
      'Hang Power Clean + Jerk',
      'Jerk',
      'Push Press',
    ],
  },
  {
    label: 'Pulls',
    exercises: ['Snatch Pull', 'Clean Pull'],
  },
  {
    label: 'Squats & Legs',
    exercises: [
      'Back Squat',
      'Front Squat',
      'Split Squat',
      'Leg Press',
      'Single Leg Romanian Deadlift',
    ],
  },
  {
    label: 'Upper Body Accessories',
    exercises: ['Prone Row', 'Single Arm Row', 'Lat Pulldown', 'Face Pull', 'Cable Curl'],
  },
  {
    label: 'Posterior Chain & Core',
    exercises: [
      'Back Extension',
      'Back Extension Iso Hold',
      'Reverse Hyper',
      'Pallof Press',
      'Leg Raise',
      'Ab Rollout',
      'Side Bend',
      'Dead Bug',
    ],
  },
  {
    // Pre-existing generic groups, kept so historical series stay loggable.
    label: 'General',
    exercises: [
      'Upper Body',
      'Lower Body',
      'Push',
      'Pull',
      'Legs',
      'Back',
      'Chest',
      'Shoulders',
      'Arms',
      'Core',
      'Lat',
      'Deadlift',
      'Squat',
      'Cardio',
      'Full Body',
    ],
  },
]
