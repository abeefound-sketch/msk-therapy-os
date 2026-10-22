#!/bin/sh
set -eu
: "${PORT:=7860}"
: "${MSK_PUBLIC_DEMO_READONLY:=1}"
export MSK_PUBLIC_DEMO_READONLY
# A disposable, synthetic-only DB is recreated on each boot. No live patient data.
DB=/app/data/demo.sqlite3
python -m msk_therapy_os init --db "$DB"
python -m msk_therapy_os seed-demo --db "$DB"
exec python -m msk_therapy_os serve --db "$DB" --host 0.0.0.0 --port "$PORT"
