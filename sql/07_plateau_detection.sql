-- Layer 7: plateau_detection
-- Detects accommodation/plateau by monitoring SPC chart tightening,
-- flat rolling average slope, and low coefficient of variation.

CREATE OR REPLACE VIEW `gen-lang-client-0937519537.Optimmax.plateau_detection` AS
WITH stats AS (
  SELECT
    *,
    -- Control band width
    ucl - lcl AS control_band_width,
    -- Session count for this exercise group
    COUNT(*) OVER (PARTITION BY exercise_group) AS total_sessions,
    -- Recent stats (last 10 sessions)
    STDDEV(total_weight) OVER (
      PARTITION BY exercise_group ORDER BY session_rank
      ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
    ) AS stddev_recent_10,
    AVG(total_weight) OVER (
      PARTITION BY exercise_group ORDER BY session_rank
      ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
    ) AS avg_recent_10,
    -- Rolling avg slope: compare current rolling_avg_7 to 10 sessions ago
    LAG(rolling_avg_7, 10) OVER (
      PARTITION BY exercise_group ORDER BY session_rank
    ) AS rolling_avg_7_10_ago,
    -- Sessions since improvement: is current weight above rolling avg?
    CASE WHEN total_weight > rolling_avg_7 THEN 0 ELSE 1 END AS below_avg_flag
  FROM
    `gen-lang-client-0937519537.Optimmax.spc_charts`
),
plateau_calc AS (
  SELECT
    *,
    -- Coefficient of variation (recent 10 sessions)
    CASE
      WHEN avg_recent_10 > 0 THEN ROUND(stddev_recent_10 / avg_recent_10 * 100, 2)
      ELSE NULL
    END AS cv_recent,
    -- Rolling avg slope as % of mean
    CASE
      WHEN rolling_avg_7_10_ago IS NOT NULL AND rolling_avg_7_10_ago > 0
      THEN ROUND((rolling_avg_7 - rolling_avg_7_10_ago) / rolling_avg_7_10_ago * 100, 2)
      ELSE NULL
    END AS rolling_avg_7_slope_pct,
    -- Count consecutive sessions below rolling average
    SUM(below_avg_flag) OVER (
      PARTITION BY exercise_group ORDER BY session_rank
      ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
    ) AS below_avg_count_5
  FROM stats
)
SELECT
  *,
  -- Plateau detection: all conditions must be true
  (
    total_sessions >= 15
    AND cv_recent IS NOT NULL AND cv_recent < 5.0
    AND rolling_avg_7_slope_pct IS NOT NULL AND ABS(rolling_avg_7_slope_pct) < 2.0
    AND below_avg_count_5 >= 5
  ) AS is_plateau,
  -- Plateau urgency
  CASE
    WHEN total_sessions >= 15
      AND cv_recent IS NOT NULL AND cv_recent < 5.0
      AND rolling_avg_7_slope_pct IS NOT NULL AND ABS(rolling_avg_7_slope_pct) < 2.0
      AND below_avg_count_5 >= 5
    THEN
      CASE
        WHEN below_avg_count_5 >= 10 THEN 'HIGH'
        ELSE 'MODERATE'
      END
    ELSE NULL
  END AS rotation_urgency
FROM plateau_calc;
