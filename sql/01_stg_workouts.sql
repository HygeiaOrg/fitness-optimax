-- Layer 1: stg_workouts
-- Clean, type-cast, and normalize the raw Google Sheets external table.
-- Source: gen-lang-client-0937519537.Optimmax.Fitness OptiMax (external Google Sheet)
--
-- Every cast is SAFE: a single malformed row in the sheet (a stray header, a
-- half-typed date, a blank line at the bottom) must not fail the whole query and
-- take the dashboard down with it. Rows without a usable date are dropped.
--
-- Strength-only scope: every row is rolled up into a catalogue entry, either an
-- Olympic lift / derivative ('Snatch', 'Hang Power Clean', ...) or the muscle
-- group it was captured under on the original sheet ('Leg, Quads', ...). A
-- specific accessory logged by name ('Back Squat') joins its muscle group, and a name
-- the catalogue doesn't know is left out. The map is generated from
-- frontend/src/data/exercises.json.
--
-- RPE is on the 0-10 scale (10 = nothing left, 9 = one rep left, ...). The
-- original sheet recorded RPE on a 1-5 scale, so its values are mapped across by
-- reps in reserve: 5 -> 10, 4 -> 9, 3 -> 8, 2 -> 7, 1 -> 6. The app logs 0-10.

CREATE OR REPLACE VIEW `gen-lang-client-0937519537.Optimmax.stg_workouts` AS
WITH sheet_rows AS (
  SELECT
    SAFE.PARSE_TIMESTAMP('%d/%m/%Y %H:%M:%S', string_field_0) AS workout_timestamp,
    SAFE.PARSE_DATE('%d/%m/%Y', string_field_1) AS workout_date,
    TRIM(string_field_2) AS athlete_name,
    string_field_3 AS raw_exercise,
    SAFE_CAST(string_field_4 AS INT64) AS sets,
    SAFE_CAST(string_field_5 AS INT64) AS total_reps,
    SAFE_CAST(REPLACE(string_field_6, ',', '') AS FLOAT64) AS total_weight,
    -- Sheet RPE was 1-5: move it onto the 0-10 scale.
    CASE
      WHEN SAFE_CAST(string_field_7 AS INT64) BETWEEN 1 AND 5 THEN SAFE_CAST(string_field_7 AS INT64) + 5
    END AS rpe
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
    exercise_group AS raw_exercise,
    sets,
    total_reps,
    total_weight,
    rpe
  FROM
    `gen-lang-client-0937519537.Optimmax.native_workouts`
),
exercise_map AS (
  -- BEGIN GENERATED exercise_map (python scripts/sync_exercises.py sql)
  SELECT raw_name, exercise_group FROM UNNEST([
    STRUCT('Ab Roll Outs' AS raw_name, 'Abdominal' AS exercise_group),
    STRUCT('Ab Rollout' AS raw_name, 'Abdominal' AS exercise_group),
    STRUCT('Abdominal' AS raw_name, 'Abdominal' AS exercise_group),
    STRUCT('Arms, Biceps' AS raw_name, 'Arms, Biceps' AS exercise_group),
    STRUCT('Arms, Triceps' AS raw_name, 'Arms, Triceps' AS exercise_group),
    STRUCT('Back / Trunk Iso\'s' AS raw_name, 'Lower Back' AS exercise_group),
    STRUCT('Back Ext' AS raw_name, 'Lower Back' AS exercise_group),
    STRUCT('Back Ext Iso Holds' AS raw_name, 'Lower Back' AS exercise_group),
    STRUCT('Back Extension' AS raw_name, 'Lower Back' AS exercise_group),
    STRUCT('Back Extension Iso Hold' AS raw_name, 'Lower Back' AS exercise_group),
    STRUCT('Back Squat' AS raw_name, 'Leg, Quads' AS exercise_group),
    STRUCT('Back Squats' AS raw_name, 'Leg, Quads' AS exercise_group),
    STRUCT('Barbell Hip Thrust' AS raw_name, 'Gluteus Maximus' AS exercise_group),
    STRUCT('Bench Press' AS raw_name, 'Upper Body, Chest' AS exercise_group),
    STRUCT('Block Power Clean' AS raw_name, 'Block Power Clean' AS exercise_group),
    STRUCT('Block Pull' AS raw_name, 'Block Pull' AS exercise_group),
    STRUCT('Cable Curl' AS raw_name, 'Arms, Biceps' AS exercise_group),
    STRUCT('Cable Curls' AS raw_name, 'Arms, Biceps' AS exercise_group),
    STRUCT('Chest' AS raw_name, 'Upper Body, Chest' AS exercise_group),
    STRUCT('Clean' AS raw_name, 'Clean' AS exercise_group),
    STRUCT('Clean & Jerk' AS raw_name, 'Clean & Jerk' AS exercise_group),
    STRUCT('Clean Pull' AS raw_name, 'Clean Pull' AS exercise_group),
    STRUCT('Copenhagen Plank' AS raw_name, 'Hip Adduction' AS exercise_group),
    STRUCT('Copenhagen Planks' AS raw_name, 'Hip Adduction' AS exercise_group),
    STRUCT('Core' AS raw_name, 'Abdominal' AS exercise_group),
    STRUCT('Db Lat Raise' AS raw_name, 'Upper Body, Lateral Delt' AS exercise_group),
    STRUCT('Db Pull Overs' AS raw_name, 'Upper Body, Lat' AS exercise_group),
    STRUCT('Dead Bug' AS raw_name, 'Abdominal' AS exercise_group),
    STRUCT('Deadbugs' AS raw_name, 'Abdominal' AS exercise_group),
    STRUCT('Deadlift' AS raw_name, 'Power, Deadlift (Inc Trap Bar)' AS exercise_group),
    STRUCT('Dumbbell Lateral Raise' AS raw_name, 'Upper Body, Lateral Delt' AS exercise_group),
    STRUCT('Dumbbell Pullover' AS raw_name, 'Upper Body, Lat' AS exercise_group),
    STRUCT('Face Pull' AS raw_name, 'Upper Body, Rear Delt' AS exercise_group),
    STRUCT('Front Squat' AS raw_name, 'Leg, Quads' AS exercise_group),
    STRUCT('Gluteus Maximus' AS raw_name, 'Gluteus Maximus' AS exercise_group),
    STRUCT('Hamstring Curl' AS raw_name, 'Legs, Hamstring' AS exercise_group),
    STRUCT('Hamstring Curls' AS raw_name, 'Legs, Hamstring' AS exercise_group),
    STRUCT('Hang Power Clean' AS raw_name, 'Hang Power Clean' AS exercise_group),
    STRUCT('Hang Power Clean + Jerk' AS raw_name, 'Hang Power Clean + Jerk' AS exercise_group),
    STRUCT('Hang Power Snatch' AS raw_name, 'Hang Power Snatch' AS exercise_group),
    STRUCT('Hang Snatch' AS raw_name, 'Hang Snatch' AS exercise_group),
    STRUCT('Hanging / Lying Leg Raise' AS raw_name, 'Abdominal' AS exercise_group),
    STRUCT('High Pull + Hang Power Snatch' AS raw_name, 'High Pull + Hang Power Snatch' AS exercise_group),
    STRUCT('Hip Abduction' AS raw_name, 'Hip Abduction' AS exercise_group),
    STRUCT('Hip Adduction' AS raw_name, 'Hip Adduction' AS exercise_group),
    STRUCT('Incline Bench Press' AS raw_name, 'Upper Body, Chest' AS exercise_group),
    STRUCT('Jerk' AS raw_name, 'Jerk' AS exercise_group),
    STRUCT('Lat' AS raw_name, 'Upper Body, Lat' AS exercise_group),
    STRUCT('Lat Pull Down' AS raw_name, 'Upper Body, Lat' AS exercise_group),
    STRUCT('Lat Pulldown' AS raw_name, 'Upper Body, Lat' AS exercise_group),
    STRUCT('Leg Extension' AS raw_name, 'Leg, Quads' AS exercise_group),
    STRUCT('Leg Press' AS raw_name, 'Leg, Quads' AS exercise_group),
    STRUCT('Leg Raise' AS raw_name, 'Abdominal' AS exercise_group),
    STRUCT('Leg, Calfs' AS raw_name, 'Leg, Calfs' AS exercise_group),
    STRUCT('Leg, Quads' AS raw_name, 'Leg, Quads' AS exercise_group),
    STRUCT('Legs, Hamstring' AS raw_name, 'Legs, Hamstring' AS exercise_group),
    STRUCT('Low Hang Power Clean + Jerk' AS raw_name, 'Low Hang Power Clean + Jerk' AS exercise_group),
    STRUCT('Low Hang Power Snatch + Snatch Balance' AS raw_name, 'Low Hang Power Snatch + Snatch Balance' AS exercise_group),
    STRUCT('Lower Back' AS raw_name, 'Lower Back' AS exercise_group),
    STRUCT('Olympic, Clean' AS raw_name, 'Clean' AS exercise_group),
    STRUCT('Olympic, Clean And Jerk' AS raw_name, 'Clean & Jerk' AS exercise_group),
    STRUCT('Olympic, Snatch' AS raw_name, 'Snatch' AS exercise_group),
    STRUCT('Pallof Press' AS raw_name, 'Abdominal' AS exercise_group),
    STRUCT('Power Clean' AS raw_name, 'Power Clean' AS exercise_group),
    STRUCT('Power Clean & Power Jerk' AS raw_name, 'Power Clean & Power Jerk' AS exercise_group),
    STRUCT('Power Clean + Jerk' AS raw_name, 'Power Clean + Jerk' AS exercise_group),
    STRUCT('Power Snatch' AS raw_name, 'Power Snatch' AS exercise_group),
    STRUCT('Power Snatch + Oh Squat' AS raw_name, 'Power Snatch + Overhead Squat' AS exercise_group),
    STRUCT('Power Snatch + Overhead Squat' AS raw_name, 'Power Snatch + Overhead Squat' AS exercise_group),
    STRUCT('Power, Clean' AS raw_name, 'Power Clean' AS exercise_group),
    STRUCT('Power, Deadlift (Inc Trap Bar)' AS raw_name, 'Power, Deadlift (Inc Trap Bar)' AS exercise_group),
    STRUCT('Prone Row' AS raw_name, 'Upper Body, Lat' AS exercise_group),
    STRUCT('Push Press' AS raw_name, 'Push Press' AS exercise_group),
    STRUCT('Push Press + Jerk' AS raw_name, 'Push Press + Jerk' AS exercise_group),
    STRUCT('Rdl\'s' AS raw_name, 'Legs, Hamstring' AS exercise_group),
    STRUCT('Reverse Hyper' AS raw_name, 'Lower Back' AS exercise_group),
    STRUCT('Reverse Hyper Ext' AS raw_name, 'Lower Back' AS exercise_group),
    STRUCT('Romanian Deadlift' AS raw_name, 'Legs, Hamstring' AS exercise_group),
    STRUCT('Sa Row' AS raw_name, 'Upper Body, Lat' AS exercise_group),
    STRUCT('Seated Press' AS raw_name, 'Upper Body, Front Delt' AS exercise_group),
    STRUCT('Seated Press Or Strict Press' AS raw_name, 'Upper Body, Front Delt' AS exercise_group),
    STRUCT('Side Bend' AS raw_name, 'Abdominal' AS exercise_group),
    STRUCT('Side Bends' AS raw_name, 'Abdominal' AS exercise_group),
    STRUCT('Single Arm Row' AS raw_name, 'Upper Body, Lat' AS exercise_group),
    STRUCT('Single Leg Romanian Deadlift' AS raw_name, 'Legs, Hamstring' AS exercise_group),
    STRUCT('Sl Rdl' AS raw_name, 'Legs, Hamstring' AS exercise_group),
    STRUCT('Snatch' AS raw_name, 'Snatch' AS exercise_group),
    STRUCT('Snatch Deadlift' AS raw_name, 'Snatch Deadlift' AS exercise_group),
    STRUCT('Snatch High Pull' AS raw_name, 'Snatch High Pull' AS exercise_group),
    STRUCT('Snatch Pull' AS raw_name, 'Snatch Pull' AS exercise_group),
    STRUCT('Split Squat' AS raw_name, 'Leg, Quads' AS exercise_group),
    STRUCT('Split Squats' AS raw_name, 'Leg, Quads' AS exercise_group),
    STRUCT('Squat' AS raw_name, 'Leg, Quads' AS exercise_group),
    STRUCT('Strict Press' AS raw_name, 'Upper Body, Front Delt' AS exercise_group),
    STRUCT('Tricep Extension' AS raw_name, 'Arms, Triceps' AS exercise_group),
    STRUCT('Tricep Extensions' AS raw_name, 'Arms, Triceps' AS exercise_group),
    STRUCT('Upper Body Traps' AS raw_name, 'Upper Body Traps' AS exercise_group),
    STRUCT('Upper Body, Chest' AS raw_name, 'Upper Body, Chest' AS exercise_group),
    STRUCT('Upper Body, Front Delt' AS raw_name, 'Upper Body, Front Delt' AS exercise_group),
    STRUCT('Upper Body, Lat' AS raw_name, 'Upper Body, Lat' AS exercise_group),
    STRUCT('Upper Body, Lateral Delt' AS raw_name, 'Upper Body, Lateral Delt' AS exercise_group),
    STRUCT('Upper Body, Rear Delt' AS raw_name, 'Upper Body, Rear Delt' AS exercise_group),
    STRUCT('Weighted Plank' AS raw_name, 'Abdominal' AS exercise_group),
    STRUCT('Weighted Planks' AS raw_name, 'Abdominal' AS exercise_group),
    STRUCT('Weighted Pull Up' AS raw_name, 'Upper Body, Lat' AS exercise_group),
    STRUCT('Weighted Pull Ups' AS raw_name, 'Upper Body, Lat' AS exercise_group)
  ])
  -- END GENERATED exercise_map
)
SELECT
  -- Fall back to midnight on the workout date when only the timestamp is unparseable,
  -- so session ordering still works.
  COALESCE(c.workout_timestamp, TIMESTAMP(c.workout_date)) AS workout_timestamp,
  c.workout_date,
  c.athlete_name,
  m.exercise_group,
  c.sets,
  c.total_reps,
  c.total_weight,
  CASE WHEN c.rpe BETWEEN 0 AND 10 THEN c.rpe END AS rpe
FROM combined c
JOIN exercise_map m
  ON INITCAP(TRIM(REGEXP_REPLACE(c.raw_exercise, r'\s+', ' '))) = m.raw_name
WHERE
  c.workout_date IS NOT NULL
  -- A session needs a load to be analysable at all.
  AND c.total_weight IS NOT NULL;
