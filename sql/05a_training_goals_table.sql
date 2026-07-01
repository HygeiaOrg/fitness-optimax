-- Config view: training_goals
-- Returns default 'HYPERTROPHY' for all groups (Free tier workaround for DML)

CREATE OR REPLACE VIEW `gen-lang-client-0937519537.Optimmax.training_goals` AS
SELECT DISTINCT INITCAP(TRIM(string_field_3)) AS exercise_group, 'HYPERTROPHY' AS training_goal
FROM `gen-lang-client-0937519537.Optimmax.Fitness OptiMax`
WHERE string_field_0 != 'Timestamp';
