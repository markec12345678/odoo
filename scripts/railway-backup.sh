#!/usr/bin/env bash
# Railway cron backup script — daily PostgreSQL dump + filestore tar.gz
# Designed to run as a Railway cron service alongside the main Odoo service.
#
# Storage options (set one in Railway variables):
#   BACKUP_S3_ENDPOINT + BACKUP_S3_BUCKET + AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY (S3-compatible: Backblaze B2, Wasabi, R2, AWS S3)
#   BACKUP_WEBHOOK_URL — POST backup to a webhook (e.g., Discord, Slack, custom endpoint)
#   BACKUP_LOCAL_ONLY=1 — keep backups in container volume (NOT recommended for production)
#
# Required Railway variables (reference variables from Postgres service):
#   PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE
#
# Optional:
#   BACKUP_RETENTION_DAYS=30 — delete local backups older than N days
#   BACKUP_PREFIX=daily — filename prefix
#   BACKUP_FILESTORE_PATH=/var/lib/odoo — Odoo filestore location
set -euo pipefail

TIMESTAMP=$(date -u +"%Y-%m-%dT%H-%M-%SZ")
BACKUP_PREFIX="${BACKUP_PREFIX:-daily}"
BACKUP_DIR="${BACKUP_DIR:-/tmp/backups}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
BACKUP_FILESTORE_PATH="${BACKUP_FILESTORE_PATH:-/var/lib/odoo}"

# Railway injects these from Postgres service (reference variables)
DB_HOST="${PGHOST:-localhost}"
DB_PORT="${PGPORT:-5432}"
DB_USER="${PGUSER:-postgres}"
DB_PASS="${PGPASSWORD:-}"
DB_NAME="${PGDATABASE:-postgres}"

mkdir -p "${BACKUP_DIR}"

BACKUP_FILENAME="${BACKUP_PREFIX}_${TIMESTAMP}.tar.gz"
BACKUP_FILE="${BACKUP_DIR}/${BACKUP_FILENAME}"
DB_DUMP_FILE="${BACKUP_DIR}/db_${TIMESTAMP}.sql"

echo "=== Railway Odoo Backup ==="
echo "Timestamp: ${TIMESTAMP}"
echo "Database:  ${DB_NAME}@${DB_HOST}:${DB_PORT}"
echo "Output:    ${BACKUP_FILE}"
echo ""

# Step 1: PostgreSQL dump
echo "[1/4] Dumping PostgreSQL database..."
PGPASSWORD="${DB_PASS}" pg_dump \
    --host="${DB_HOST}" \
    --port="${DB_PORT}" \
    --username="${DB_USER}" \
    --format=plain \
    --no-owner \
    --no-privileges \
    --no-password \
    "${DB_NAME}" > "${DB_DUMP_FILE}"

DUMP_SIZE=$(du -h "${DB_DUMP_FILE}" | cut -f1)
echo "    ✓ Database dump: ${DUMP_SIZE}"

# Step 2: Compress with filestore
echo "[2/4] Creating compressed archive..."
WORK_DIR=$(mktemp -d)
trap "rm -rf ${WORK_DIR}" EXIT

ARCHIVE_DIR="${WORK_DIR}/${TIMESTAMP}"
mkdir -p "${ARCHIVE_DIR}"

mv "${DB_DUMP_FILE}" "${ARCHIVE_DIR}/database.sql"

# Filestore (only if mounted and non-empty)
if [ -d "${BACKUP_FILESTORE_PATH}/filestore" ]; then
    echo "    -> Including filestore..."
    cp -r "${BACKUP_FILESTORE_PATH}/filestore" "${ARCHIVE_DIR}/filestore"
fi

# Odoo config (if exists)
[ -f "/etc/odoo/odoo.conf" ] && cp "/etc/odoo/odoo.conf" "${ARCHIVE_DIR}/odoo.conf"

# Manifest
cat > "${ARCHIVE_DIR}/MANIFEST" <<EOF
backup_date=${TIMESTAMP}
backup_type=${BACKUP_PREFIX}
odoo_db_name=${DB_NAME}
railway_service=odoo
project=si-hr-tourism-suite
version=v19.0.12.0
EOF

tar -czf "${BACKUP_FILE}" -C "${WORK_DIR}" "${TIMESTAMP}"
ARCHIVE_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
echo "    ✓ Archive: ${ARCHIVE_SIZE}"

# Step 3: Upload to external storage (if configured)
echo "[3/4] Uploading to external storage..."

UPLOAD_STATUS="skipped"

# Option A: S3-compatible storage (Backblaze B2, Wasabi, Cloudflare R2, AWS S3)
if [ -n "${BACKUP_S3_BUCKET:-}" ] && [ -n "${AWS_ACCESS_KEY_ID:-}" ] && [ -n "${AWS_SECRET_ACCESS_KEY:-}" ]; then
    S3_ENDPOINT="${BACKUP_S3_ENDPOINT:-https://s3.amazonaws.com}"
    S3_REGION="${BACKUP_S3_REGION:-us-east-1}"
    S3_BUCKET="${BACKUP_S3_BUCKET}"
    S3_KEY="odoo-backups/${BACKUP_FILENAME}"

    echo "    -> Uploading to S3: ${S3_BUCKET}/${S3_KEY}"

    # Use AWS CLI if available, otherwise curl with sigv4 (complex, recommend installing aws-cli)
    if command -v aws >/dev/null 2>&1; then
        aws s3 cp "${BACKUP_FILE}" "s3://${S3_BUCKET}/${S3_KEY}" \
            --endpoint-url="${S3_ENDPOINT}" \
            --region="${S3_REGION}" \
            && UPLOAD_STATUS="s3"
    else
        echo "    ⚠ aws-cli not installed — install with: pip install awscli"
        echo "    Falling back to local-only storage"
        UPLOAD_STATUS="s3-failed-no-awscli"
    fi
fi

# Option B: Webhook (POST backup file to a URL)
if [ -n "${BACKUP_WEBHOOK_URL:-}" ] && [ "${UPLOAD_STATUS}" = "skipped" ]; then
    echo "    -> Uploading to webhook: ${BACKUP_WEBHOOK_URL}"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST \
        -H "X-Backup-Timestamp: ${TIMESTAMP}" \
        -H "X-Backup-Filename: ${BACKUP_FILENAME}" \
        -F "file=@${BACKUP_FILE}" \
        "${BACKUP_WEBHOOK_URL}" || echo "000")

    if [ "${HTTP_CODE}" = "200" ] || [ "${HTTP_CODE}" = "201" ] || [ "${HTTP_CODE}" = "204" ]; then
        UPLOAD_STATUS="webhook"
        echo "    ✓ Webhook upload: HTTP ${HTTP_CODE}"
    else
        echo "    ⚠ Webhook upload failed: HTTP ${HTTP_CODE}"
        UPLOAD_STATUS="webhook-failed"
    fi
fi

# Option C: Local only (NOT recommended)
if [ "${UPLOAD_STATUS}" = "skipped" ]; then
    if [ "${BACKUP_LOCAL_ONLY:-0}" = "1" ]; then
        echo "    ⚠ Local-only mode — backup kept in container (lost on redeploy!)"
        UPLOAD_STATUS="local-only"
    else
        echo "    ⚠ No external storage configured — backup kept locally only"
        echo "    Configure BACKUP_S3_BUCKET or BACKUP_WEBHOOK_URL for offsite storage"
        UPLOAD_STATUS="local-only-warning"
    fi
fi

# Step 4: Cleanup old local backups
echo "[4/4] Cleaning up old backups..."
DELETED_COUNT=$(find "${BACKUP_DIR}" -name "${BACKUP_PREFIX}_*.tar.gz" -mtime "+${BACKUP_RETENTION_DAYS}" -delete -print | wc -l)
echo "    ✓ Deleted ${DELETED_COUNT} old backup(s) (older than ${BACKUP_RETENTION_DAYS} days)"

# Summary
echo ""
echo "=== Backup Summary ==="
echo "Status:      ${UPLOAD_STATUS}"
echo "Archive:     ${BACKUP_FILE} (${ARCHIVE_SIZE})"
echo "DB dump:     ${DUMP_SIZE}"
echo "Completed:   $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Optional: notify on failure via webhook
if [[ "${UPLOAD_STATUS}" == *"failed"* ]] || [[ "${UPLOAD_STATUS}" == *"warning"* ]]; then
    if [ -n "${ALERT_WEBHOOK_URL:-}" ]; then
        curl -s -o /dev/null -X POST \
            -H "Content-Type: application/json" \
            -d "{\"text\":\"⚠ Odoo backup warning: ${UPLOAD_STATUS} at ${TIMESTAMP}\"}" \
            "${ALERT_WEBHOOK_URL}" || true
    fi
fi

echo ""
echo "✅ Backup complete"
