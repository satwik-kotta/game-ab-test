-- Data quality: row count, duplicates, impossible values, extreme outliers
SELECT COUNT(*) AS players,
       COUNT(DISTINCT userid) AS distinct_players,
       SUM(CASE WHEN sum_gamerounds < 0 THEN 1 ELSE 0 END) AS negative_rounds,
       SUM(CASE WHEN NOT retention_1 AND retention_7 THEN 1 ELSE 0 END) AS d7_without_d1,
       MAX(sum_gamerounds) AS max_rounds,
       percentile_cont(0.99) WITHIN GROUP (ORDER BY sum_gamerounds) AS p99_rounds
FROM players;

-- The top players by rounds, to spot data-entry outliers
SELECT userid, version, sum_gamerounds,
       RANK() OVER (ORDER BY sum_gamerounds DESC) AS rnk
FROM players ORDER BY sum_gamerounds DESC LIMIT 5;
