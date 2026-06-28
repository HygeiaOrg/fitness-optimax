-- Layer 4: spc_charts
-- I-MR Control Charts with Nelson Rules for out-of-control detection.
-- Uses Moving Range method (MR-bar / d2) for process sigma estimation.

CREATE OR REPLACE VIEW `gen-lang-client-0937519537.Optimmax.spc_charts` AS
WITH moving_range AS (
  SELECT
    *,
    -- Moving Range: absolute difference between consecutive sessions
    ABS(total_weight - LAG(total_weight) OVER (
      PARTITION BY exercise_group ORDER BY session_rank
    )) AS moving_range
  FROM
    `gen-lang-client-0937519537.Optimmax.spc_rolling_averages`
),
control_limits AS (
  SELECT
    *,
    -- MR-bar: average moving range per exercise group
    AVG(moving_range) OVER (PARTITION BY exercise_group) AS mr_bar,
    -- Process mean (centre line)
    AVG(total_weight) OVER (PARTITION BY exercise_group) AS cl
  FROM moving_range
),
spc AS (
  SELECT
    *,
    -- Estimated sigma from MR-bar / d2 (d2 = 1.128 for n=2)
    mr_bar / 1.128 AS estimated_sigma,
    -- I-Chart control limits
    cl + 3 * (mr_bar / 1.128) AS ucl,
    GREATEST(0, cl - 3 * (mr_bar / 1.128)) AS lcl,
    -- Zone boundaries
    cl + 2 * (mr_bar / 1.128) AS zone_a_upper,
    cl - 2 * (mr_bar / 1.128) AS zone_a_lower,
    cl + 1 * (mr_bar / 1.128) AS zone_b_upper,
    cl - 1 * (mr_bar / 1.128) AS zone_b_lower,
    -- MR-Chart control limits
    mr_bar AS mr_cl,
    3.267 * mr_bar AS mr_ucl,
    0.0 AS mr_lcl
  FROM control_limits
),
nelson_rules AS (
  SELECT
    *,
    -- Nelson Rule 1: Point beyond 3-sigma
    (total_weight > ucl OR total_weight < lcl) AS signal_rule_1,

    -- Nelson Rule 2: 9 consecutive points on same side of CL
    CASE
      WHEN COUNT(CASE WHEN total_weight > cl THEN 1 END) OVER (
        PARTITION BY exercise_group ORDER BY session_rank
        ROWS BETWEEN 8 PRECEDING AND CURRENT ROW
      ) = 9 THEN TRUE
      WHEN COUNT(CASE WHEN total_weight < cl THEN 1 END) OVER (
        PARTITION BY exercise_group ORDER BY session_rank
        ROWS BETWEEN 8 PRECEDING AND CURRENT ROW
      ) = 9 THEN TRUE
      ELSE FALSE
    END AS signal_rule_2,

    -- Nelson Rule 3: 6 consecutive points steadily increasing or decreasing
    CASE
      WHEN total_weight > LAG(total_weight, 1) OVER (PARTITION BY exercise_group ORDER BY session_rank)
       AND LAG(total_weight, 1) OVER (PARTITION BY exercise_group ORDER BY session_rank) >
           LAG(total_weight, 2) OVER (PARTITION BY exercise_group ORDER BY session_rank)
       AND LAG(total_weight, 2) OVER (PARTITION BY exercise_group ORDER BY session_rank) >
           LAG(total_weight, 3) OVER (PARTITION BY exercise_group ORDER BY session_rank)
       AND LAG(total_weight, 3) OVER (PARTITION BY exercise_group ORDER BY session_rank) >
           LAG(total_weight, 4) OVER (PARTITION BY exercise_group ORDER BY session_rank)
       AND LAG(total_weight, 4) OVER (PARTITION BY exercise_group ORDER BY session_rank) >
           LAG(total_weight, 5) OVER (PARTITION BY exercise_group ORDER BY session_rank)
      THEN TRUE
      WHEN total_weight < LAG(total_weight, 1) OVER (PARTITION BY exercise_group ORDER BY session_rank)
       AND LAG(total_weight, 1) OVER (PARTITION BY exercise_group ORDER BY session_rank) <
           LAG(total_weight, 2) OVER (PARTITION BY exercise_group ORDER BY session_rank)
       AND LAG(total_weight, 2) OVER (PARTITION BY exercise_group ORDER BY session_rank) <
           LAG(total_weight, 3) OVER (PARTITION BY exercise_group ORDER BY session_rank)
       AND LAG(total_weight, 3) OVER (PARTITION BY exercise_group ORDER BY session_rank) <
           LAG(total_weight, 4) OVER (PARTITION BY exercise_group ORDER BY session_rank)
       AND LAG(total_weight, 4) OVER (PARTITION BY exercise_group ORDER BY session_rank) <
           LAG(total_weight, 5) OVER (PARTITION BY exercise_group ORDER BY session_rank)
      THEN TRUE
      ELSE FALSE
    END AS signal_rule_3,

    -- Nelson Rule 5: 2 of 3 consecutive points in Zone A or beyond
    CASE
      WHEN (
        CAST(total_weight > zone_a_upper OR total_weight < zone_a_lower AS INT64) +
        CAST(LAG(total_weight, 1) OVER (PARTITION BY exercise_group ORDER BY session_rank) > zone_a_upper
          OR LAG(total_weight, 1) OVER (PARTITION BY exercise_group ORDER BY session_rank) < zone_a_lower AS INT64) +
        CAST(LAG(total_weight, 2) OVER (PARTITION BY exercise_group ORDER BY session_rank) > zone_a_upper
          OR LAG(total_weight, 2) OVER (PARTITION BY exercise_group ORDER BY session_rank) < zone_a_lower AS INT64)
      ) >= 2 THEN TRUE
      ELSE FALSE
    END AS signal_rule_5
  FROM spc
)
SELECT
  *,
  (signal_rule_1 OR signal_rule_2 OR signal_rule_3 OR signal_rule_5) AS is_out_of_control
FROM nelson_rules;
