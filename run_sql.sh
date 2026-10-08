#!/usr/bin/env bash
# Usage: ./run_sql.sh <database>   (needs a running PostgreSQL and psql on PATH)
set -e
DB=${1:-games}
for f in sql/0*.sql; do echo "== $f"; psql -d "$DB" -f "$f"; done
