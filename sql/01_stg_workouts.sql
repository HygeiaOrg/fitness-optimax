-- Layer 1: stg_workouts
-- Clean, type-cast, and normalize the raw Google Sheets external table.
-- Source: gen-lang-client-0937519537.Optimmax.Fitness OptiMax (external Google Sheet)
--
-- Every cast is SAFE: a single malformed row in the sheet (a stray header, a
-- half-typed date, a blank line at the bottom) must not fail the whole query and
-- take the dashboard down with it. Rows without a usable date are dropped.

CREATE OR REPLACE VIEW `gen-lang-client-0937519537.Optimmax.stg_workouts` AS
WITH sheet_rows AS (
  SELECT
    SAFE.PARSE_TIMESTAMP('%d/%m/%Y %H:%M:%S', string_field_0) AS workout_timestamp,
    SAFE.PARSE_DATE('%d/%m/%Y', string_field_1) AS workout_date,
    TRIM(string_field_2) AS athlete_name,
    INITCAP(TRIM(string_field_3)) AS exercise_group,
    SAFE_CAST(string_field_4 AS INT64) AS sets,
    SAFE_CAST(string_field_5 AS INT64) AS total_reps,
    SAFE_CAST(REPLACE(string_field_6, ',', '') AS FLOAT64) AS total_weight,
    SAFE_CAST(string_field_7 AS INT64) AS rpe
  FROM
    `gen-lang-client-0937519537.Optimmax.Fitness OptiMax`
  WHERE
    string_field_0 != 'Timestamp'
),
combined AS (
  SELECT * FROM sheet_rows

  UNION ALL

  SELECT
    workout_timestamp,
    workout_date,
    athlete_name,
    INITCAP(TRIM(exercise_group)) AS exercise_group,
    sets,
    total_reps,
    total_weight,
    rpe
  FROM
    `gen-lang-client-0937519537.Optimmax.native_workouts`
)
SELECT
  -- Fall back to midnight on the workout date when only the timestamp is unparseable,
  -- so session ordering still works.
  COALESCE(workout_timestamp, TIMESTAMP(workout_date)) AS workout_timestamp,
  workout_date,
  athlete_name,
  exercise_group,
  sets,
  total_reps,
  total_weight,
  rpe
FROM combined
WHERE
  workout_date IS NOT NULL
  AND exercise_group IS NOT NULL
  AND exercise_group != ''
  -- A session needs a load to be analysable at all.
  AND total_weight IS NOT NULL;
