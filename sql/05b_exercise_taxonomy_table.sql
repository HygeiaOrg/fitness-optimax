-- Config table: exercise_taxonomy
-- Maps exercise groups to muscle groups and alternative exercise modes.

CREATE TABLE IF NOT EXISTS `gen-lang-client-0937519537.Optimmax.exercise_taxonomy` (
  muscle_group STRING NOT NULL,
  exercise_mode STRING NOT NULL,
  exercise_group_match STRING NOT NULL,
  alternative_modes STRING,  -- JSON array of alternatives
  stimulus_type STRING       -- 'COMPOUND' or 'ISOLATION'
);

-- Seed with known exercise groups and suggestions
INSERT INTO `gen-lang-client-0937519537.Optimmax.exercise_taxonomy`
  (muscle_group, exercise_mode, exercise_group_match, alternative_modes, stimulus_type)
VALUES
  ('Chest', 'Flat Press', 'Upper Body, Chest', '["Incline Press", "Dumbbell Fly", "Cable Crossover", "Weighted Dips"]', 'COMPOUND'),
  ('Lats', 'Lat Pulldown/Row', 'Upper Body, Lat', '["Pull-ups", "Bent-over Row", "T-bar Row", "Single-arm Cable Row"]', 'COMPOUND'),
  ('Quads', 'Leg Press/Squat', 'Leg, Quads', '["Front Squat", "Bulgarian Split Squat", "Hack Squat", "Leg Extension"]', 'COMPOUND'),
  ('Biceps', 'Curls', 'Arms, Biceps', '["Hammer Curls", "Preacher Curls", "Incline Dumbbell Curls", "Cable Curls"]', 'ISOLATION'),
  ('Triceps', 'Pushdowns', 'Arms, Triceps', '["Overhead Extension", "Skull Crushers", "Close-grip Bench Press", "Dips"]', 'ISOLATION'),
  ('Rear Delt', 'Reverse Fly', 'Upper Body, Rear Delt', '["Face Pulls", "Reverse Pec Deck", "Bent-over Lateral Raise"]', 'ISOLATION'),
  ('Hamstrings', 'Leg Curl', 'Legs, Hamstring', '["Romanian Deadlift", "Nordic Curl", "Good Morning", "Glute-Ham Raise"]', 'COMPOUND'),
  ('Front Delt', 'Front Raise', 'Upper Body, Front Delt', '["Overhead Press", "Arnold Press", "Landmine Press"]', 'COMPOUND'),
  ('Lateral Delt', 'Lateral Raise', 'Upper Body, Lateral Delt', '["Cable Lateral Raise", "Machine Lateral Raise", "Upright Row"]', 'ISOLATION'),
  ('Calves', 'Calf Raise', 'Leg, Calfs', '["Seated Calf Raise", "Donkey Calf Raise", "Single-leg Calf Raise"]', 'ISOLATION'),
  ('Glutes', 'Hip Thrust', 'Gluteus Maximus', '["Cable Kickback", "Sumo Deadlift", "Step-ups", "Glute Bridge"]', 'COMPOUND'),
  ('Lower Back', 'Back Extension', 'Lower Back', '["Reverse Hyper", "Good Morning", "Superman Hold"]', 'ISOLATION'),
  ('Traps', 'Shrugs', 'Upper Body Traps', '["Farmers Walk", "Rack Pulls", "Face Pulls"]', 'COMPOUND'),
  ('Full Body', 'Deadlift', 'Power, Deadlift (Inc Trap Bar)', '["Sumo Deadlift", "Trap Bar Deadlift", "Rack Pull", "Block Pull"]', 'COMPOUND'),
  ('Core', 'Crunches', 'Abdominal', '["Hanging Leg Raise", "Cable Woodchop", "Ab Wheel", "Plank Variations"]', 'ISOLATION'),
  ('Olympic', 'Clean', 'Olympic, Clean', '["Power Clean", "Hang Clean", "Clean Pull"]', 'COMPOUND'),
  ('Olympic', 'Snatch', 'Olympic, Snatch', '["Power Snatch", "Hang Snatch", "Snatch Pull"]', 'COMPOUND'),
  ('Olympic', 'Clean and Jerk', 'Olympic, Clean And Jerk', '["Push Press", "Push Jerk", "Split Jerk"]', 'COMPOUND'),
  ('Hip', 'Hip Abduction', 'Hip Abduction', '["Banded Side Walk", "Cable Abduction", "Side-lying Leg Raise"]', 'ISOLATION'),
  ('Hip', 'Hip Adduction', 'Hip Adduction', '["Cable Adduction", "Copenhagen Plank", "Sumo Squat"]', 'ISOLATION'),
  ('Full Body', 'Power Clean', 'Power, Clean', '["Hang Clean", "Clean and Press", "Clean Pull"]', 'COMPOUND')
;
