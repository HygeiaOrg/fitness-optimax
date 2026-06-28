-- Layer 1: stg_workouts
-- Clean, type-cast, and normalize the raw Google Sheets external table.
-- Source: gen-lang-client-0937519537.Optimmax.Fitness OptiMax (external Google Sheet)

CREATE OR REPLACE VIEW `gen-lang-client-0937519537.Optimmax.stg_workouts` AS
SELECT
  PARSE_TIMESTAMP('%d/%m/%Y %H:%M:%S', string_field_0) AS workout_timestamp,
  PARSE_DATE('%d/%m/%Y', string_field_1) AS workout_date,
  TRIM(string_field_2) AS athlete_name,
  INITCAP(TRIM(string_field_3)) AS exercise_group,
  CAST(string_field_4 AS INT64) AS sets,
  CAST(string_field_5 AS INT64) AS total_reps,
  CAST(REPLACE(string_field_6, ',', '') AS FLOAT64) AS total_weight,
  SAFE_CAST(string_field_7 AS INT64) AS rpe
FROM
  `gen-lang-client-0937519537.Optimmax.Fitness OptiMax`
WHERE
  string_field_0 != 'Timestamp';
