-- Layer: athletes
-- One row per registered athlete (see issue #18). weight_category is a plain
-- mutable field, not append-only history like one_rep_maxes: an athlete
-- moving up/down a class just overwrites it.

CREATE TABLE IF NOT EXISTS `gen-lang-client-0937519537.Optimmax.athletes` (
    athlete_id STRING NOT NULL,
    name STRING NOT NULL,
    email STRING NOT NULL,
    sex_category STRING NOT NULL,     -- 'male' | 'female'
    age_category STRING NOT NULL,     -- 'under_18' | '18_25' | '26_35' | 'masters_35_plus'
    weight_category STRING NOT NULL,  -- valid values depend on sex_category — see api/models.py WEIGHT_CLASSES
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);
