#!/bin/bash
# Railway entrypoint — parses DATABASE_URL and starts Odoo
# Railway auto-provides: DATABASE_URL, PORT
set -e

echo "=== SI/HR Odoo 19 on Railway ==="
echo "DATABASE_URL: ${DATABASE_URL:+set (hidden)}"
echo "PORT: ${PORT:-8080}"

# Parse DATABASE_URL if provided
if [ -n "$DATABASE_URL" ]; then
    # Remove postgresql:// prefix
    DB_URL_CLEAN="${DATABASE_URL#postgresql://}"
    
    # Extract user
    DB_USER="${DB_URL_CLEAN%%:*}"
    
    # Extract password (between : and @)
    DB_REMAINING="${DB_URL_CLEAN#*:}"
    DB_PASS="${DB_REMAINING%%@*}"
    
    # Extract host:port/db
    DB_HOSTPORT="${DB_REMAINING#*@}"
    DB_HOST="${DB_HOSTPORT%%:*}"
    
    # Extract port (if present)
    if [[ "$DB_HOSTPORT" == *:* ]]; then
        DB_PORT="${DB_HOSTPORT#*:}"
        DB_PORT="${DB_PORT%%/*}"
    else
        DB_PORT="5432"
    fi
    
    # Extract database name
    DB_NAME="${DB_HOSTPORT#*/}"
    DB_NAME="${DB_NAME%%\?*}"  # Remove query params if any
    
    echo "DB Host: $DB_HOST"
    echo "DB Port: $DB_PORT"
    echo "DB User: $DB_USER"
    echo "DB Name: $DB_NAME"
else
    echo "WARNING: DATABASE_URL not set — Odoo will use default config"
    DB_HOST="db"
    DB_PORT="5432"
    DB_USER="odoo"
    DB_PASS="odoo"
    DB_NAME="postgres"
fi

# Determine port (Railway provides PORT, default 8080)
HTTP_PORT="${PORT:-8080}"
echo "HTTP Port: $HTTP_PORT"

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
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
    --database=si_odoo \
    --db_filter=^si_odoo$ \
    --proxy-mode \
    --workers=2 \
    --max-cron-threads=1 \
    --http-port="$HTTP_PORT" \
    --limit-memory-soft=1073741824 \
    --limit-memory-hard=1342177280 \
    --limit-time-cpu=600 \
    --limit-time-real=1200 \
    --without-demo=all \
    --log-level=info \
    --save
