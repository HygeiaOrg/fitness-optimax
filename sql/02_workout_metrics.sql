-- Layer 2: workout_metrics
-- Calculate derived per-session metrics on top of the staging view.

CREATE OR REPLACE VIEW `gen-lang-client-0937519537.Optimmax.workout_metrics` AS
SELECT
  *,
  total_weight / NULLIF(total_reps, 0) AS avg_weight_per_rep,
  total_weight / NULLIF(sets, 0) AS avg_weight_per_set,
  CAST(total_reps AS FLOAT64) / NULLIF(sets, 0) AS avg_reps_per_set,
  total_weight AS volume_index,
  ROW_NUMBER() OVER (
    PARTITION BY exercise_group
    ORDER BY workout_date, workout_timestamp
  ) AS session_rank
FROM
  `gen-lang-client-0937519537.Optimmax.stg_workouts`;
