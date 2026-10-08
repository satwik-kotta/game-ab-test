-- Experiment readout by variant, with traffic share (for the sample-ratio check) and lift vs control
WITH v AS (
  SELECT version,
         COUNT(*)                     AS players,
         AVG(retention_1::int)        AS d1,
         AVG(retention_7::int)        AS d7,
         AVG(sum_gamerounds)          AS mean_rounds,
         percentile_cont(0.5) WITHIN GROUP (ORDER BY sum_gamerounds) AS median_rounds
  FROM players
  WHERE sum_gamerounds < 10000          -- drop one extreme outlier (49,854 rounds)
  GROUP BY version
)
SELECT version, players,
       ROUND(100.0 * players / SUM(players) OVER (), 2)                         AS traffic_pct,
       ROUND(100.0 * d1, 2) AS d1_pct,
       ROUND(100.0 * d7, 2) AS d7_pct,
       ROUND(100.0 * (d1 / FIRST_VALUE(d1) OVER (ORDER BY version) - 1), 2)     AS d1_rel_lift_vs_gate30_pct,
       ROUND(100.0 * (d7 / FIRST_VALUE(d7) OVER (ORDER BY version) - 1), 2)     AS d7_rel_lift_vs_gate30_pct,
       ROUND(mean_rounds, 1) AS mean_rounds, median_rounds
FROM v ORDER BY version;
