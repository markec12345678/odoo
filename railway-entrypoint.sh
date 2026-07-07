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

# Sentinel file — marks that the DB has been initialized with base module
INIT_FLAG="/var/lib/odoo/.db-initialized"

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

# Common Odoo CLI flags (used both for init and serve phases)
COMMON_FLAGS=(
    --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons
    --db_host="$DB_HOST"
    --db_port="$DB_PORT"
    --db_user="$DB_USER"
    --db_password="$DB_PASS"
    --database="$DB_NAME"
    --without-demo=True
    --log-level=info
)

# First-run initialization: install base module + our custom SI/HR modules
# This creates the Odoo schema in the empty Railway-provided DB.
# On subsequent runs, the sentinel file exists and we skip this step.
if [ ! -f "$INIT_FLAG" ]; then
    echo "=== First run: initializing database with base + SI/HR modules ==="
    echo "This will take 3-5 minutes for the first install..."
    python3 /railway-odoo-launcher.py \
        "${COMMON_FLAGS[@]}" \
        --init=base \
        --stop-after-init \
        --load=web \
        --workers=0 \
        --max-cron-threads=1 \
        --limit-memory-soft=536870912 \
        --limit-memory-hard=805306368 \
        --limit-time-cpu=1800 \
        --limit-time-real=3600
    echo "Database initialization complete!"
    touch "$INIT_FLAG"
    echo "Sentinel file created at $INIT_FLAG"
fi

# Asset bundle cleanup — required because Railway ephemeral filesystem
# loses filestore on every redeploy. Without this, browsers get HTTP 500 on
# /web/assets/* because the bundle files referenced in DB no longer exist.
# Fix: delete stale asset bundle references from ir_attachment; Odoo will
# regenerate them on first request to /web/* endpoints.
echo "=== Cleaning stale asset bundle references (ephemeral filesystem workaround) ==="
PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c \
    "DELETE FROM ir_attachment WHERE url LIKE '/web/assets/%';" 2>&1 | grep -v "^DELETE" || true
echo "Stale asset references cleared — Odoo will regenerate bundles on first request"

# Start Odoo in normal server mode
# NO proxy-mode (Railway handles proxy), NO workers (simpler startup)
# Use --http-port to match Railway PORT
# Note: --without-demo expects boolean True/False in Odoo 19 (not 'all')
echo "Starting Odoo on port $HTTP_PORT..."
exec python3 /railway-odoo-launcher.py \
    "${COMMON_FLAGS[@]}" \
    --http-interface=0.0.0.0 \
    --http-port="$HTTP_PORT" \
    --workers=0 \
    --max-cron-threads=1 \
    --limit-memory-soft=536870912 \
    --limit-memory-hard=805306368 \
    --limit-time-cpu=300 \
    --limit-time-real=600
