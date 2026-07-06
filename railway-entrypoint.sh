#!/bin/bash
# Railway entrypoint — starts Odoo with Railway-provided variables
# Railway provides: PGUSER, PGPASSWORD, PGHOST, PGPORT, PGDATABASE, PORT
set -e

echo "=== SI/HR Odoo 19 on Railway ==="
echo "PORT: ${PORT:-8080}"

# Railway injects standard PG* variables via reference variables
DB_HOST="${PGHOST:-localhost}"
DB_PORT="${PGPORT:-5432}"
DB_USER="${PGUSER:-postgres}"
DB_PASS="${PGPASSWORD:-}"
DB_NAME="${PGDATABASE:-postgres}"

echo "DB Host: $DB_HOST"
echo "DB Port: $DB_PORT"
echo "DB User: $DB_USER"
echo "DB Name: $DB_NAME"

# Determine port (Railway provides PORT, default 8080)
HTTP_PORT="${PORT:-8080}"
echo "HTTP Port: $HTTP_PORT"

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."
for i in $(seq 1 30); do
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" 2>/dev/null; then
        echo "PostgreSQL is ready!"
        break
    fi
    echo "  Attempt $i/30 — waiting..."
    sleep 2
done

# Start Odoo
echo "Starting Odoo on port $HTTP_PORT..."
exec odoo \
    --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons \
    --db_host="$DB_HOST" \
    --db_port="$DB_PORT" \
    --db_user="$DB_USER" \
    --db_password="$DB_PASS" \
    --database="$DB_NAME" \
    --proxy-mode \
    --workers=2 \
    --max-cron-threads=1 \
    --http-interface 0.0.0.0 \
    --http-port="$HTTP_PORT" \
    --limit-memory-soft=1073741824 \
    --limit-memory-hard=1342177280 \
    --limit-time-cpu=600 \
    --limit-time-real=1200 \
    --without-demo \
    --log-level=info
