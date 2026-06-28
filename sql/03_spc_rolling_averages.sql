-- Layer 3: spc_rolling_averages
-- 3/5/7 rolling averages + moving average crossover detection per exercise group.

CREATE OR REPLACE VIEW `gen-lang-client-0937519537.Optimmax.spc_rolling_averages` AS
WITH rolling AS (
  SELECT
    *,
    -- Rolling averages
    AVG(total_weight) OVER (
      PARTITION BY exercise_group ORDER BY session_rank
      ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS rolling_avg_3,
    AVG(total_weight) OVER (
      PARTITION BY exercise_group ORDER BY session_rank
      ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
    ) AS rolling_avg_5,
    AVG(total_weight) OVER (
      PARTITION BY exercise_group ORDER BY session_rank
      ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS rolling_avg_7
  FROM
    `gen-lang-client-0937519537.Optimmax.workout_metrics`
),
crossover AS (
  SELECT
    *,
    -- Current spread between MAs
    rolling_avg_3 - rolling_avg_5 AS ma3_vs_ma5,
    rolling_avg_3 - rolling_avg_7 AS ma3_vs_ma7,
    -- Previous spread (for crossover detection)
    LAG(rolling_avg_3 - rolling_avg_5) OVER (
      PARTITION BY exercise_group ORDER BY session_rank
    ) AS prev_ma3_vs_ma5,
    LAG(rolling_avg_3 - rolling_avg_7) OVER (
      PARTITION BY exercise_group ORDER BY session_rank
    ) AS prev_ma3_vs_ma7,
    -- Boolean: is 3-MA currently above?
    rolling_avg_3 > rolling_avg_5 AS ma3_above_ma5,
    rolling_avg_3 > rolling_avg_7 AS ma3_above_ma7
  FROM rolling
)
SELECT
  *,
  -- Golden cross: 3-MA just crossed ABOVE
  (ma3_above_ma5 = TRUE AND prev_ma3_vs_ma5 <= 0) AS golden_cross_5,
  (ma3_above_ma7 = TRUE AND prev_ma3_vs_ma7 <= 0) AS golden_cross_7,
  (ma3_above_ma5 = TRUE AND prev_ma3_vs_ma5 <= 0
   AND ma3_above_ma7 = TRUE AND prev_ma3_vs_ma7 <= 0) AS golden_cross,
  -- Regression cross: 3-MA just dropped BELOW
  (ma3_above_ma5 = FALSE AND prev_ma3_vs_ma5 > 0) AS regression_cross_5,
  (ma3_above_ma7 = FALSE AND prev_ma3_vs_ma7 > 0) AS regression_cross_7,
  (ma3_above_ma5 = FALSE AND prev_ma3_vs_ma5 > 0
   AND ma3_above_ma7 = FALSE AND prev_ma3_vs_ma7 > 0) AS regression_cross,
  -- Momentum signal
  CASE
    WHEN rolling_avg_3 > rolling_avg_5 AND rolling_avg_5 > rolling_avg_7 THEN 'IMPROVING'
    WHEN rolling_avg_3 < rolling_avg_5 AND rolling_avg_5 < rolling_avg_7 THEN 'DECLINING'
    ELSE 'MIXED'
  END AS momentum_signal
FROM crossover;
