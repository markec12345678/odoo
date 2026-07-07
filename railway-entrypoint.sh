#!/bin/bash
# Railway entrypoint — starts Odoo with Railway-provided variables
set -e

echo "=== SI/HR Odoo 19 on Railway ==="

# Railway injects standard PG* variables via reference variables
DB_HOST="${PGHOST:-localhost}"
DB_PORT="${PGPORT:-5432}"
DB_USER="${PGUSER:-postgres}"
DB_PASS="${PGPASSWORD:-}"
DB_NAME="${PGDATABASE:-postgres}"

# Railway provides PORT — Odoo MUST listen on this
HTTP_PORT="${PORT:-8080}"

echo "DB Host: $DB_HOST"
echo "DB Port: $DB_PORT"
echo "DB User: $DB_USER"
echo "DB Name: $DB_NAME"
echo "HTTP Port: $HTTP_PORT"

# Wait for PostgreSQL
echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."
for i in $(seq 1 60); do
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" 2>/dev/null; then
        echo "PostgreSQL is ready!"
        break
    fi
    echo "  Attempt $i/60 — waiting..."
    sleep 2
done

# Start Odoo — NO proxy-mode (Railway handles proxy), NO workers (simpler startup)
# Use --http-port to match Railway PORT
echo "Starting Odoo on port $HTTP_PORT..."
exec odoo \
    --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons \
    --db_host="$DB_HOST" \
    --db_port="$DB_PORT" \
    --db_user="$DB_USER" \
    --db_password="$DB_PASS" \
    --database="$DB_NAME" \
    --http-port="$HTTP_PORT" \
    --workers=0 \
    --max-cron-threads=1 \
    --limit-memory-soft=536870912 \
    --limit-memory-hard=805306368 \
    --limit-time-cpu=300 \
    --limit-time-real=600 \
    --without-demo=all \
    --log-level=info
