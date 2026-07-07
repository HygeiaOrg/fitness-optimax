-- Config table: training_goals
-- Stores the user's declared training goal per exercise group.
-- Frontend writes to this and backend reads from it.

CREATE TABLE IF NOT EXISTS `gen-lang-client-0937519537.Optimmax.training_goals` (
  exercise_group STRING NOT NULL,
  training_goal STRING NOT NULL,  -- 'STRENGTH' or 'HYPERTROPHY'
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Seed with defaults (HYPERTROPHY for all groups)
-- Only insert if table is empty
INSERT INTO `gen-lang-client-0937519537.Optimmax.training_goals` (exercise_group, training_goal)
SELECT exercise_group, 'HYPERTROPHY' AS training_goal
FROM (
  SELECT DISTINCT INITCAP(TRIM(string_field_3)) AS exercise_group
  FROM `gen-lang-client-0937519537.Optimmax.Fitness OptiMax`
  WHERE string_field_0 != 'Timestamp'
)
WHERE exercise_group NOT IN (
  SELECT exercise_group FROM `gen-lang-client-0937519537.Optimmax.training_goals`
);
