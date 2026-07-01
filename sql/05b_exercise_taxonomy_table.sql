-- Config view: exercise_taxonomy
-- Maps exercise groups to muscle groups and alternative exercise modes. (View workaround)

CREATE OR REPLACE VIEW `gen-lang-client-0937519537.Optimmax.exercise_taxonomy` AS
SELECT 'Chest' AS muscle_group, 'Flat Press' AS exercise_mode, 'Upper Body, Chest' AS exercise_group_match, '["Incline Press", "Dumbbell Fly", "Cable Crossover", "Weighted Dips"]' AS alternative_modes, 'COMPOUND' AS stimulus_type UNION ALL
SELECT 'Lats', 'Lat Pulldown/Row', 'Upper Body, Lat', '["Pull-ups", "Bent-over Row", "T-bar Row", "Single-arm Cable Row"]', 'COMPOUND' UNION ALL
SELECT 'Quads', 'Leg Press/Squat', 'Leg, Quads', '["Front Squat", "Bulgarian Split Squat", "Hack Squat", "Leg Extension"]', 'COMPOUND' UNION ALL
SELECT 'Biceps', 'Curls', 'Arms, Biceps', '["Hammer Curls", "Preacher Curls", "Incline Dumbbell Curls", "Cable Curls"]', 'ISOLATION' UNION ALL
SELECT 'Triceps', 'Pushdowns', 'Arms, Triceps', '["Overhead Extension", "Skull Crushers", "Close-grip Bench Press", "Dips"]', 'ISOLATION' UNION ALL
SELECT 'Rear Delt', 'Reverse Fly', 'Upper Body, Rear Delt', '["Face Pulls", "Reverse Pec Deck", "Bent-over Lateral Raise"]', 'ISOLATION' UNION ALL
SELECT 'Hamstrings', 'Leg Curl', 'Legs, Hamstring', '["Romanian Deadlift", "Nordic Curl", "Good Morning", "Glute-Ham Raise"]', 'COMPOUND' UNION ALL
SELECT 'Front Delt', 'Front Raise', 'Upper Body, Front Delt', '["Overhead Press", "Arnold Press", "Landmine Press"]', 'COMPOUND' UNION ALL
SELECT 'Lateral Delt', 'Lateral Raise', 'Upper Body, Lateral Delt', '["Cable Lateral Raise", "Machine Lateral Raise", "Upright Row"]', 'ISOLATION' UNION ALL
SELECT 'Calves', 'Calf Raise', 'Leg, Calfs', '["Seated Calf Raise", "Donkey Calf Raise", "Single-leg Calf Raise"]', 'ISOLATION' UNION ALL
SELECT 'Glutes', 'Hip Thrust', 'Gluteus Maximus', '["Cable Kickback", "Sumo Deadlift", "Step-ups", "Glute Bridge"]', 'COMPOUND' UNION ALL
SELECT 'Lower Back', 'Back Extension', 'Lower Back', '["Reverse Hyper", "Good Morning", "Superman Hold"]', 'ISOLATION' UNION ALL
SELECT 'Traps', 'Shrugs', 'Upper Body Traps', '["Farmers Walk", "Rack Pulls", "Face Pulls"]', 'COMPOUND' UNION ALL
SELECT 'Full Body', 'Deadlift', 'Power, Deadlift (Inc Trap Bar)', '["Sumo Deadlift", "Trap Bar Deadlift", "Rack Pull", "Block Pull"]', 'COMPOUND' UNION ALL
SELECT 'Core', 'Crunches', 'Abdominal', '["Hanging Leg Raise", "Cable Woodchop", "Ab Wheel", "Plank Variations"]', 'ISOLATION' UNION ALL
SELECT 'Olympic', 'Clean', 'Olympic, Clean', '["Power Clean", "Hang Clean", "Clean Pull"]', 'COMPOUND' UNION ALL
SELECT 'Olympic', 'Snatch', 'Olympic, Snatch', '["Power Snatch", "Hang Snatch", "Snatch Pull"]', 'COMPOUND' UNION ALL
SELECT 'Olympic', 'Clean and Jerk', 'Olympic, Clean And Jerk', '["Push Press", "Push Jerk", "Split Jerk"]', 'COMPOUND' UNION ALL
SELECT 'Hip', 'Hip Abduction', 'Hip Abduction', '["Banded Side Walk", "Cable Abduction", "Side-lying Leg Raise"]', 'ISOLATION' UNION ALL
SELECT 'Hip', 'Hip Adduction', 'Hip Adduction', '["Cable Adduction", "Copenhagen Plank", "Sumo Squat"]', 'ISOLATION' UNION ALL
SELECT 'Full Body', 'Power Clean', 'Power, Clean', '["Hang Clean", "Clean and Press", "Clean Pull"]', 'COMPOUND';
