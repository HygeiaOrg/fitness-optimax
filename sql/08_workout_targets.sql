-- Layer 5: workout_targets
-- Generates next-session targets and actionable alerts per exercise group,
-- driven by training goal, calibrated RPE trends, rolling averages, and plateau detection.

CREATE OR REPLACE VIEW `gen-lang-client-0937519537.Optimmax.workout_targets` AS
WITH base_data AS (
  SELECT
    c.*,
    cal.calibrated_rpe,
    cal.rpe_confidence,
    plat.is_plateau,
    plat.rotation_suggestion,
    COALESCE(tg.training_goal, 'HYPERTROPHY') AS training_goal
  FROM
    `gen-lang-client-0937519537.Optimmax.spc_charts` c
  LEFT JOIN
    `gen-lang-client-0937519537.Optimmax.rpe_calibration` cal
    ON c.exercise_group = cal.exercise_group AND c.session_rank = cal.session_rank
  LEFT JOIN
    `gen-lang-client-0937519537.Optimmax.plateau_detection` plat
    ON c.exercise_group = plat.exercise_group AND c.session_rank = plat.session_rank
  LEFT JOIN
    `gen-lang-client-0937519537.Optimmax.training_goals` tg
    ON c.exercise_group = tg.exercise_group
),
with_trends AS (
  SELECT
    *,
    -- Use calibrated RPE if we have confidence, otherwise fallback to raw RPE
    COALESCE(
      CASE WHEN rpe_confidence IN ('MEDIUM', 'HIGH') THEN calibrated_rpe ELSE CAST(rpe AS FLOAT64) END,
      0
    ) AS effective_rpe,
    -- 3-session average of effective RPE
    AVG(
      COALESCE(
        CASE WHEN rpe_confidence IN ('MEDIUM', 'HIGH') THEN calibrated_rpe ELSE CAST(rpe AS FLOAT64) END,
        0
      )
    ) OVER (
      PARTITION BY exercise_group ORDER BY session_rank
      ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS rpe_avg_3,
    -- Identify the most recent session for each exercise group
    MAX(session_rank) OVER (PARTITION BY exercise_group) AS latest_session_rank,
    -- Days since last session for staleness alert
    DATE_DIFF(CURRENT_DATE(), workout_date, DAY) AS days_since_last_session,
    -- Get avg reps over last 4 sessions for targets
    ROUND(AVG(total_reps) OVER (
      PARTITION BY exercise_group ORDER BY session_rank
      ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
    )) AS target_reps_baseline,
    ROUND(AVG(sets) OVER (
      PARTITION BY exercise_group ORDER BY session_rank
      ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
    )) AS target_sets_baseline
  FROM base_data
),
latest_only AS (
  SELECT *
  FROM with_trends
  WHERE session_rank = latest_session_rank
),
decision_matrix AS (
  SELECT
    *,
    -- Goal-Aware Decision Logic
    CASE
      WHEN is_plateau = TRUE THEN 'REVIEW_REQUIRED'
      WHEN is_out_of_control = TRUE THEN 'REVIEW_REQUIRED'

      -- STRENGTH GOAL
      WHEN training_goal = 'STRENGTH' THEN
        CASE
          WHEN rpe_avg_3 <= 2.5 THEN 'INCREASE_LOAD'
          WHEN rpe_avg_3 <= 3.5 THEN 'SLIGHT_INCREASE'
          WHEN rpe_avg_3 <= 4.5 AND avg_reps_per_set <= 5 THEN 'MAINTAIN'
          WHEN rpe_avg_3 <= 4.5 AND avg_reps_per_set > 5 THEN 'NUDGE_REDUCE_REPS'
          WHEN rpe_avg_3 > 4.5 AND avg_reps_per_set <= 2 THEN 'MAINTAIN'
          WHEN rpe_avg_3 > 4.5 AND avg_reps_per_set <= 5 THEN 'MICRO_INCREASE'
          WHEN rpe_avg_3 > 4.5 AND avg_reps_per_set > 5 THEN 'NUDGE_REDUCE_REPS'
          ELSE 'MAINTAIN'
        END

      -- HYPERTROPHY GOAL
      WHEN training_goal = 'HYPERTROPHY' THEN
        CASE
          WHEN rpe_avg_3 <= 2.5 THEN 'INCREASE_LOAD'
          WHEN rpe_avg_3 <= 3.5 AND avg_reps_per_set >= 8 AND avg_reps_per_set <= 15 THEN 'MAINTAIN'
          WHEN rpe_avg_3 <= 3.5 AND avg_reps_per_set < 8 THEN 'NUDGE_INCREASE_REPS'
          WHEN rpe_avg_3 <= 4.5 AND avg_reps_per_set >= 8 AND avg_reps_per_set <= 15 THEN 'SLIGHT_INCREASE'
          WHEN rpe_avg_3 <= 4.5 AND avg_reps_per_set < 8 THEN 'NUDGE_INCREASE_REPS'
          WHEN rpe_avg_3 > 4.5 AND avg_reps_per_set <= 2 THEN 'NUDGE_INCREASE_REPS_SIGNIFICANTLY'
          WHEN rpe_avg_3 > 4.5 AND avg_reps_per_set <= 7 THEN 'NUDGE_INCREASE_REPS'
          WHEN rpe_avg_3 > 4.5 AND avg_reps_per_set <= 15 THEN 'MICRO_INCREASE'
          WHEN rpe_avg_3 > 4.5 AND avg_reps_per_set > 15 THEN 'INCREASE_LOAD'
          ELSE 'MAINTAIN'
        END
      ELSE 'MAINTAIN'
    END AS logic_decision
  FROM latest_only
),
targets_calc AS (
  SELECT
    *,
    -- Target Multipliers
    CASE
      WHEN logic_decision = 'INCREASE_LOAD' THEN 1.05
      WHEN logic_decision = 'SLIGHT_INCREASE' THEN 1.025
      WHEN logic_decision = 'MICRO_INCREASE' THEN 1.01
      WHEN logic_decision IN ('NUDGE_REDUCE_REPS') THEN 1.05
      WHEN logic_decision IN ('NUDGE_INCREASE_REPS') THEN 0.95
      WHEN logic_decision IN ('NUDGE_INCREASE_REPS_SIGNIFICANTLY') THEN 0.85
      ELSE 1.0
    END AS weight_multiplier,

    -- Target Reps adjustments
    CASE
      WHEN logic_decision IN ('NUDGE_REDUCE_REPS') THEN LEAST(5.0, target_reps_baseline)
      WHEN logic_decision IN ('NUDGE_INCREASE_REPS', 'NUDGE_INCREASE_REPS_SIGNIFICANTLY') THEN GREATEST(8.0, target_reps_baseline)
      ELSE target_reps_baseline
    END AS target_reps,

    -- Target Sets (keep consistent)
    target_sets_baseline AS target_sets

  FROM decision_matrix
),
final_calc AS (
  SELECT
    *,
    rolling_avg_5 * weight_multiplier AS target_total_weight,
    -- Determine target weight per rep
    (rolling_avg_5 * weight_multiplier) / NULLIF(target_reps, 0) AS target_weight_per_rep,
    
    -- Goal Alignment
    CASE
      WHEN training_goal = 'STRENGTH' AND avg_reps_per_set > 8 THEN FALSE
      WHEN training_goal = 'HYPERTROPHY' AND avg_reps_per_set < 6 THEN FALSE
      ELSE TRUE
    END AS goal_aligned,
    
    -- Staleness
    (days_since_last_session > 14) AS staleness_alert
  FROM targets_calc
)
SELECT
  exercise_group,
  training_goal,
  workout_date AS last_session_date,
  days_since_last_session,
  staleness_alert,
  total_weight AS last_total_weight,
  rolling_avg_5,
  avg_reps_per_set AS last_avg_reps_per_set,
  rpe_avg_3,
  is_plateau,
  
  -- Master Alert Output
  CASE
    WHEN is_plateau = TRUE THEN 'EXERCISE_ROTATION'
    ELSE logic_decision
  END AS alert_type,
  
  -- Master Message Output
  CASE
    WHEN is_plateau = TRUE THEN CONCAT('Plateau detected! Consider switching to: ', COALESCE(rotation_suggestion, 'a variation.'))
    WHEN logic_decision = 'INCREASE_LOAD' THEN 'Great capacity! Increase load by 5-10%.'
    WHEN logic_decision = 'SLIGHT_INCREASE' THEN 'Room for overload. Increase load by 2.5-5%.'
    WHEN logic_decision = 'MICRO_INCREASE' THEN 'Failed with volume. Micro increase 1-2.5%.'
    WHEN logic_decision = 'NUDGE_REDUCE_REPS' THEN 'Too many reps for strength goal. Increase weight and lower reps (1-5).'
    WHEN logic_decision = 'NUDGE_INCREASE_REPS' THEN 'Too heavy for hypertrophy. Reduce weight and aim for 8-15 reps.'
    WHEN logic_decision = 'NUDGE_INCREASE_REPS_SIGNIFICANTLY' THEN 'Maxing out at low reps builds strength, not size. Reduce weight significantly.'
    WHEN is_out_of_control = TRUE THEN 'Process shift detected (Nelson Rule). Review required.'
    ELSE 'Maintain optimal training stimulus.'
  END AS alert_message,
  
  goal_aligned,
  target_total_weight,
  target_sets,
  target_reps,
  target_weight_per_rep
FROM final_calc;
