-- D7 retention by engagement bucket and variant (descriptive only: rounds played is itself
-- affected by the gate, so these cuts are not causal estimates)
SELECT CASE WHEN sum_gamerounds < 30 THEN 'a) <30 rounds'
            WHEN sum_gamerounds < 40 THEN 'b) 30-39'
            WHEN sum_gamerounds < 100 THEN 'c) 40-99'
            ELSE 'd) 100+' END AS bucket,
       version, COUNT(*) AS players,
       ROUND(100.0 * AVG(retention_7::int), 2) AS d7_pct
FROM players WHERE sum_gamerounds < 10000
GROUP BY 1, 2 ORDER BY 1, 2;
