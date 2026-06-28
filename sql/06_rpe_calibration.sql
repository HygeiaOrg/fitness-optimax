-- Layer 6: rpe_calibration
-- Adaptive RPE feedback loop: learns the user's RPE bias by correlating
-- declared RPE with actual performance outcomes in the next session.

CREATE OR REPLACE VIEW `gen-lang-client-0937519537.Optimmax.rpe_calibration` AS
WITH with_next_session AS (
  SELECT
    *,
    -- What happened in the NEXT session for this exercise group?
    LEAD(total_weight) OVER (
      PARTITION BY exercise_group ORDER BY session_rank
    ) AS next_total_weight,
    -- Previous session's RPE (used for outcome evaluation)
    LAG(rpe) OVER (
      PARTITION BY exercise_group ORDER BY session_rank
    ) AS prev_rpe,
    LAG(total_weight) OVER (
      PARTITION BY exercise_group ORDER BY session_rank
    ) AS prev_total_weight
  FROM
    `gen-lang-client-0937519537.Optimmax.spc_charts`
),
with_outcome AS (
  SELECT
    *,
    -- Weight change from previous session (%)
    CASE
      WHEN prev_total_weight IS NOT NULL AND prev_total_weight > 0
      THEN ROUND((total_weight - prev_total_weight) / prev_total_weight * 100, 1)
      ELSE NULL
    END AS weight_delta_pct,
    -- Evaluate accuracy of the PREVIOUS session's RPE declaration
    CASE
      -- No previous RPE to evaluate
      WHEN prev_rpe IS NULL THEN NULL
      -- Low RPE (<=2): accurate if weight increased, under-reported if it didn't
      WHEN prev_rpe <= 2 AND total_weight > prev_total_weight THEN 'ACCURATE'
      WHEN prev_rpe <= 2 AND total_weight <= prev_total_weight THEN 'UNDER_REPORTED'
      -- Moderate RPE (3): conservative if weight increased, accurate if maintained
      WHEN prev_rpe = 3 AND total_weight > prev_total_weight * 1.025 THEN 'UNDER_REPORTED'
      WHEN prev_rpe = 3 THEN 'ACCURATE'
      -- Target RPE (4): accurate if maintained, under-reported if decreased
      WHEN prev_rpe = 4 AND total_weight < prev_total_weight * 0.975 THEN 'UNDER_REPORTED'
      WHEN prev_rpe = 4 THEN 'ACCURATE'
      -- High RPE (5): over-reported if weight increased, accurate otherwise
      WHEN prev_rpe = 5 AND total_weight > prev_total_weight * 1.025 THEN 'OVER_REPORTED'
      WHEN prev_rpe = 5 THEN 'ACCURATE'
      ELSE 'ACCURATE'
    END AS rpe_outcome
  FROM with_next_session
),
with_bias AS (
  SELECT
    *,
    -- Running bias: rolling average of bias signals over last 10 sessions
    AVG(
      CASE
        WHEN rpe_outcome = 'UNDER_REPORTED' THEN -0.5
        WHEN rpe_outcome = 'OVER_REPORTED' THEN 0.5
        ELSE 0
      END
    ) OVER (
      PARTITION BY exercise_group ORDER BY session_rank
      ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
    ) AS rpe_bias_running,
    -- Count of non-null RPE sessions for confidence calculation
    COUNT(rpe) OVER (
      PARTITION BY exercise_group ORDER BY session_rank
      ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS rpe_session_count
  FROM with_outcome
)
SELECT
  *,
  -- Calibrated RPE: adjust raw RPE by the running bias
  CASE
    WHEN rpe IS NOT NULL THEN ROUND(rpe + rpe_bias_running, 1)
    ELSE NULL
  END AS calibrated_rpe,
  -- Confidence level for the calibration
  CASE
    WHEN rpe_session_count < 5 THEN 'LOW'
    WHEN rpe_session_count <= 15 THEN 'MEDIUM'
    ELSE 'HIGH'
  END AS rpe_confidence
FROM with_bias;
