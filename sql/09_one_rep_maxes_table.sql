-- Config table: one_rep_maxes
-- Each athlete's recorded 1RM per lift, append-only. The newest row per
-- (athlete_name, lift) is the current 1RM; older rows are kept as history.
-- `lift` is a catalogue name (see one_rm_lifts / one_rm_base in
-- frontend/src/data/exercises.json), e.g. 'Snatch', 'Back Squat'.
-- Written by POST /api/one-rep-maxes, read by GET /api/one-rep-maxes.

CREATE TABLE IF NOT EXISTS `gen-lang-client-0937519537.Optimmax.one_rep_maxes` (
  athlete_name STRING NOT NULL,
  lift STRING NOT NULL,
  one_rm_kg FLOAT64 NOT NULL,
  recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
