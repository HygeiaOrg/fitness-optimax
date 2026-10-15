-- Layer 5: workout_targets
-- Generates next-session targets and actionable alerts per exercise group,
-- driven by calibrated RPE trends, rolling averages, and plateau detection.
-- Strength is the only training objective: low reps (1-5 per set), load first.

CREATE OR REPLACE VIEW `gen-lang-client-0937519537.Optimmax.workout_targets` AS
WITH base_data AS (
  SELECT
    c.*,
    cal.calibrated_rpe,
    cal.rpe_confidence,
    plat.is_plateau
  FROM
    `gen-lang-client-0937519537.Optimmax.spc_charts` c
  LEFT JOIN
    `gen-lang-client-0937519537.Optimmax.rpe_calibration` cal
    ON c.exercise_group = cal.exercise_group AND c.session_rank = cal.session_rank
  LEFT JOIN
    `gen-lang-client-0937519537.Optimmax.plateau_detection` plat
    ON c.exercise_group = plat.exercise_group AND c.session_rank = plat.session_rank
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
    )) AS target_sets_baseline,
    -- Estimated 1RM (Epley) from the session's average kg per rep and reps per
    -- set. Beyond 12 reps a set the estimate is too loose to be useful.
    CASE
      WHEN avg_reps_per_set > 0 AND avg_reps_per_set <= 12
      THEN avg_weight_per_rep * (1 + avg_reps_per_set / 30)
    END AS session_estimated_1rm
  FROM base_data
),
with_best AS (
  SELECT
    *,
    MAX(session_estimated_1rm) OVER (PARTITION BY exercise_group) AS best_estimated_1rm
  FROM with_trends
),
latest_only AS (
  SELECT *
  FROM with_best
  WHERE session_rank = latest_session_rank
),
decision_matrix AS (
  SELECT
    *,
    -- Strength decision logic (RPE on the 0-10 scale, 10 = nothing left)
    CASE
      WHEN is_plateau = TRUE THEN 'REVIEW_REQUIRED'
      WHEN is_out_of_control = TRUE THEN 'REVIEW_REQUIRED'
      WHEN rpe_avg_3 <= 7.5 THEN 'INCREASE_LOAD'
      WHEN rpe_avg_3 <= 8.5 THEN 'SLIGHT_INCREASE'
      WHEN rpe_avg_3 <= 9.5 AND avg_reps_per_set <= 5 THEN 'MAINTAIN'
      WHEN rpe_avg_3 <= 9.5 AND avg_reps_per_set > 5 THEN 'NUDGE_REDUCE_REPS'
      WHEN rpe_avg_3 > 9.5 AND avg_reps_per_set <= 2 THEN 'MAINTAIN'
      WHEN rpe_avg_3 > 9.5 AND avg_reps_per_set <= 5 THEN 'MICRO_INCREASE'
      WHEN rpe_avg_3 > 9.5 AND avg_reps_per_set > 5 THEN 'NUDGE_REDUCE_REPS'
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
      WHEN logic_decision = 'NUDGE_REDUCE_REPS' THEN 1.05
      ELSE 1.0
    END AS weight_multiplier,

    -- Target Reps adjustments
    CASE
      -- Total reps for the session: cap at 5 per set.
      WHEN logic_decision = 'NUDGE_REDUCE_REPS' THEN LEAST(5.0 * target_sets_baseline, target_reps_baseline)
      ELSE target_reps_baseline
    END AS target_reps,

    -- Target Sets (keep consistent)
    target_sets_baseline AS target_sets

  FROM decision_matrix
),
final_calc AS (
  SELECT
    *,
    -- Fewer reps: progress the bar weight, not the session volume, otherwise
    -- the same tonnage over fewer reps would demand an unrealistic jump.
    CASE
      WHEN logic_decision = 'NUDGE_REDUCE_REPS' THEN avg_weight_per_rep * weight_multiplier * target_reps
      ELSE rolling_avg_5 * weight_multiplier
    END AS target_total_weight,
    CASE
      WHEN logic_decision = 'NUDGE_REDUCE_REPS' THEN avg_weight_per_rep * weight_multiplier
      ELSE (rolling_avg_5 * weight_multiplier) / NULLIF(target_reps, 0)
    END AS target_weight_per_rep,

    -- Staleness
    (days_since_last_session > 14) AS staleness_alert
  FROM targets_calc
)
-- The API reads these columns directly, so NULLs are coalesced away here:
-- `is_plateau` arrives via a LEFT JOIN and `avg_reps_per_set` divides by sets.
SELECT
  exercise_group,
  workout_date AS last_session_date,
  days_since_last_session,
  COALESCE(staleness_alert, FALSE) AS staleness_alert,
  total_weight AS last_total_weight,
  rolling_avg_5,
  COALESCE(avg_reps_per_set, 0) AS last_avg_reps_per_set,
  rpe_avg_3,
  COALESCE(is_plateau, FALSE) AS is_plateau,
  
  -- Master Alert Output
  CASE
    WHEN is_plateau = TRUE THEN 'EXERCISE_ROTATION'
    ELSE logic_decision
  END AS alert_type,
  
  -- Master Message Output
  CASE
    WHEN is_plateau = TRUE THEN 'Plateau detected! Consider switching to a variation.'
    WHEN logic_decision = 'INCREASE_LOAD' THEN 'Great capacity! Increase load by 5-10%.'
    WHEN logic_decision = 'SLIGHT_INCREASE' THEN 'Room for overload. Increase load by 2.5-5%.'
    WHEN logic_decision = 'MICRO_INCREASE' THEN 'Failed with volume. Micro increase 1-2.5%.'
    WHEN logic_decision = 'NUDGE_REDUCE_REPS' THEN 'Too many reps for strength. Increase weight and lower reps (1-5 per set).'
    WHEN is_out_of_control = TRUE THEN 'Process shift detected (Nelson Rule). Review required.'
    ELSE 'Maintain optimal training stimulus.'
  END AS alert_message,
  
  target_total_weight,
  CAST(target_sets AS INT64) AS target_sets,
  CAST(target_reps AS INT64) AS target_reps,
  target_weight_per_rep,
  avg_weight_per_rep AS last_avg_weight_per_rep,
  session_estimated_1rm AS estimated_1rm,
  best_estimated_1rm
FROM final_calc;
