-- Layer 0: native_workouts
-- This is a native BigQuery table where the API directly inserts new workouts.

CREATE TABLE IF NOT EXISTS `gen-lang-client-0937519537.Optimmax.native_workouts` (
    workout_timestamp TIMESTAMP,
    workout_date DATE,
    athlete_name STRING,
    exercise_group STRING,
    sets INT64,
    total_reps INT64,
    total_weight FLOAT64,
    rpe INT64
);
