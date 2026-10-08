-- Player engagement before looking at the experiment
WITH buckets AS (
  SELECT *,
    CASE WHEN sum_gamerounds = 0   THEN '0 rounds'
         WHEN sum_gamerounds < 30  THEN '1-29'
         WHEN sum_gamerounds < 40  THEN '30-39'
         WHEN sum_gamerounds < 100 THEN '40-99'
         ELSE '100+' END AS bucket,
    CASE WHEN sum_gamerounds = 0   THEN 1
         WHEN sum_gamerounds < 30  THEN 2
         WHEN sum_gamerounds < 40  THEN 3
         WHEN sum_gamerounds < 100 THEN 4
         ELSE 5 END AS bucket_order
  FROM players
)
SELECT bucket,
       COUNT(*)                                             AS players,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)   AS pct_players,
       ROUND(100.0 * AVG(retention_1::int), 1)              AS d1_pct,
       ROUND(100.0 * AVG(retention_7::int), 1)              AS d7_pct
FROM buckets GROUP BY bucket, bucket_order ORDER BY bucket_order;

-- Overall KPIs
SELECT COUNT(*) AS players,
       ROUND(100.0 * AVG(retention_1::int), 2) AS d1_pct,
       ROUND(100.0 * AVG(retention_7::int), 2) AS d7_pct,
       ROUND(100.0 * AVG((retention_1 AND NOT retention_7)::int), 2) AS d1_but_not_d7_pct,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY sum_gamerounds) AS median_rounds,
       ROUND(AVG(sum_gamerounds), 1) AS mean_rounds
FROM players;
