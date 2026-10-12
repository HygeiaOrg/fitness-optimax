-- Config table: exercise_taxonomy
-- Maps exercise groups to muscle groups and alternative exercise modes.

CREATE TABLE IF NOT EXISTS `gen-lang-client-0937519537.Optimmax.exercise_taxonomy` (
  muscle_group STRING NOT NULL,
  exercise_mode STRING NOT NULL,
  exercise_group_match STRING NOT NULL,
  alternative_modes STRING,  -- JSON array of alternatives
  stimulus_type STRING       -- 'COMPOUND' or 'ISOLATION'
);

-- Seed with known exercise groups and suggestions.
-- Only seeds an empty table, so re-running deploy_views.py (CI does on sql/ changes)
-- never duplicates rows.
INSERT INTO `gen-lang-client-0937519537.Optimmax.exercise_taxonomy`
  (muscle_group, exercise_mode, exercise_group_match, alternative_modes, stimulus_type)
SELECT * FROM UNNEST([
  STRUCT<muscle_group STRING, exercise_mode STRING, exercise_group_match STRING, alternative_modes STRING, stimulus_type STRING>('Chest', 'Flat Press', 'Upper Body, Chest', '["Incline Press", "Dumbbell Fly", "Cable Crossover", "Weighted Dips"]', 'COMPOUND'),
  STRUCT<muscle_group STRING, exercise_mode STRING, exercise_group_match STRING, alternative_modes STRING, stimulus_type STRING>('Lats', 'Lat Pulldown/Row', 'Upper Body, Lat', '["Pull-ups", "Bent-over Row", "T-bar Row", "Single-arm Cable Row"]', 'COMPOUND'),
  STRUCT<muscle_group STRING, exercise_mode STRING, exercise_group_match STRING, alternative_modes STRING, stimulus_type STRING>('Quads', 'Leg Press/Squat', 'Leg, Quads', '["Front Squat", "Bulgarian Split Squat", "Hack Squat", "Leg Extension"]', 'COMPOUND'),
  STRUCT<muscle_group STRING, exercise_mode STRING, exercise_group_match STRING, alternative_modes STRING, stimulus_type STRING>('Biceps', 'Curls', 'Arms, Biceps', '["Hammer Curls", "Preacher Curls", "Incline Dumbbell Curls", "Cable Curls"]', 'ISOLATION'),
  STRUCT<muscle_group STRING, exercise_mode STRING, exercise_group_match STRING, alternative_modes STRING, stimulus_type STRING>('Triceps', 'Pushdowns', 'Arms, Triceps', '["Overhead Extension", "Skull Crushers", "Close-grip Bench Press", "Dips"]', 'ISOLATION'),
  STRUCT<muscle_group STRING, exercise_mode STRING, exercise_group_match STRING, alternative_modes STRING, stimulus_type STRING>('Rear Delt', 'Reverse Fly', 'Upper Body, Rear Delt', '["Face Pulls", "Reverse Pec Deck", "Bent-over Lateral Raise"]', 'ISOLATION'),
  STRUCT<muscle_group STRING, exercise_mode STRING, exercise_group_match STRING, alternative_modes STRING, stimulus_type STRING>('Hamstrings', 'Leg Curl', 'Legs, Hamstring', '["Romanian Deadlift", "Nordic Curl", "Good Morning", "Glute-Ham Raise"]', 'COMPOUND'),
  STRUCT<muscle_group STRING, exercise_mode STRING, exercise_group_match STRING, alternative_modes STRING, stimulus_type STRING>('Front Delt', 'Front Raise', 'Upper Body, Front Delt', '["Overhead Press", "Arnold Press", "Landmine Press"]', 'COMPOUND'),
  STRUCT<muscle_group STRING, exercise_mode STRING, exercise_group_match STRING, alternative_modes STRING, stimulus_type STRING>('Lateral Delt', 'Lateral Raise', 'Upper Body, Lateral Delt', '["Cable Lateral Raise", "Machine Lateral Raise", "Upright Row"]', 'ISOLATION'),
  STRUCT<muscle_group STRING, exercise_mode STRING, exercise_group_match STRING, alternative_modes STRING, stimulus_type STRING>('Calves', 'Calf Raise', 'Leg, Calfs', '["Seated Calf Raise", "Donkey Calf Raise", "Single-leg Calf Raise"]', 'ISOLATION'),
  STRUCT<muscle_group STRING, exercise_mode STRING, exercise_group_match STRING, alternative_modes STRING, stimulus_type STRING>('Glutes', 'Hip Thrust', 'Gluteus Maximus', '["Cable Kickback", "Sumo Deadlift", "Step-ups", "Glute Bridge"]', 'COMPOUND'),
  STRUCT<muscle_group STRING, exercise_mode STRING, exercise_group_match STRING, alternative_modes STRING, stimulus_type STRING>('Lower Back', 'Back Extension', 'Lower Back', '["Reverse Hyper", "Good Morning", "Superman Hold"]', 'ISOLATION'),
  STRUCT<muscle_group STRING, exercise_mode STRING, exercise_group_match STRING, alternative_modes STRING, stimulus_type STRING>('Traps', 'Shrugs', 'Upper Body Traps', '["Farmers Walk", "Rack Pulls", "Face Pulls"]', 'COMPOUND'),
  STRUCT<muscle_group STRING, exercise_mode STRING, exercise_group_match STRING, alternative_modes STRING, stimulus_type STRING>('Full Body', 'Deadlift', 'Power, Deadlift (Inc Trap Bar)', '["Sumo Deadlift", "Trap Bar Deadlift", "Rack Pull", "Block Pull"]', 'COMPOUND'),
  STRUCT<muscle_group STRING, exercise_mode STRING, exercise_group_match STRING, alternative_modes STRING, stimulus_type STRING>('Core', 'Crunches', 'Abdominal', '["Hanging Leg Raise", "Cable Woodchop", "Ab Wheel", "Plank Variations"]', 'ISOLATION'),
  STRUCT<muscle_group STRING, exercise_mode STRING, exercise_group_match STRING, alternative_modes STRING, stimulus_type STRING>('Olympic', 'Clean', 'Olympic, Clean', '["Power Clean", "Hang Clean", "Clean Pull"]', 'COMPOUND'),
  STRUCT<muscle_group STRING, exercise_mode STRING, exercise_group_match STRING, alternative_modes STRING, stimulus_type STRING>('Olympic', 'Snatch', 'Olympic, Snatch', '["Power Snatch", "Hang Snatch", "Snatch Pull"]', 'COMPOUND'),
  STRUCT<muscle_group STRING, exercise_mode STRING, exercise_group_match STRING, alternative_modes STRING, stimulus_type STRING>('Olympic', 'Clean and Jerk', 'Olympic, Clean And Jerk', '["Push Press", "Push Jerk", "Split Jerk"]', 'COMPOUND'),
  STRUCT<muscle_group STRING, exercise_mode STRING, exercise_group_match STRING, alternative_modes STRING, stimulus_type STRING>('Hip', 'Hip Abduction', 'Hip Abduction', '["Banded Side Walk", "Cable Abduction", "Side-lying Leg Raise"]', 'ISOLATION'),
  STRUCT<muscle_group STRING, exercise_mode STRING, exercise_group_match STRING, alternative_modes STRING, stimulus_type STRING>('Hip', 'Hip Adduction', 'Hip Adduction', '["Cable Adduction", "Copenhagen Plank", "Sumo Squat"]', 'ISOLATION'),
  STRUCT<muscle_group STRING, exercise_mode STRING, exercise_group_match STRING, alternative_modes STRING, stimulus_type STRING>('Full Body', 'Power Clean', 'Power, Clean', '["Hang Clean", "Clean and Press", "Clean Pull"]', 'COMPOUND')
])
WHERE NOT EXISTS (SELECT 1 FROM `gen-lang-client-0937519537.Optimmax.exercise_taxonomy`);
