-- Load the Cookie Cats experiment: one row per player who installed during the test window
DROP TABLE IF EXISTS players;
CREATE TABLE players (
  userid          INTEGER PRIMARY KEY,
  version         TEXT    NOT NULL CHECK (version IN ('gate_30','gate_40')),
  sum_gamerounds  INTEGER NOT NULL,   -- game rounds played in the first 14 days after install
  retention_1     BOOLEAN NOT NULL,   -- came back and played 1 day after install
  retention_7     BOOLEAN NOT NULL    -- came back and played 7 days after install
);
\copy players FROM 'data/cookie_cats.csv' WITH (FORMAT csv, HEADER true)
