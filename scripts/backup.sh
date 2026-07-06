#!/usr/bin/env bash
# Slovenian Odoo backup script — daily database + filestore + configs.
set -euo pipefail
ODOO_DB_NAME="${ODOO_DB_NAME:-si_odoo}"
ODOO_DB_USER="${ODOO_DB_USER:-odoo}"
ODOO_DB_HOST="${ODOO_DB_HOST:-db}"
ODOO_DB_PORT="${ODOO_DB_PORT:-5432}"
ODOO_FILESTORE="${ODOO_FILESTORE:-/var/lib/odoo}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/odoo}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")
BACKUP_PREFIX="${BACKUP_PREFIX:-daily}"
BACKUP_FILE="${BACKUP_DIR}/${BACKUP_PREFIX}_${TIMESTAMP}.tar.gz"
mkdir -p "${BACKUP_DIR}"
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Starting backup of '${ODOO_DB_NAME}' to ${BACKUP_FILE}"
DB_DUMP_FILE="${BACKUP_DIR}/db_${TIMESTAMP}.sql"
echo "  -> Dumping PostgreSQL database..."
PGPASSWORD="${PGPASSWORD:-}" pg_dump --host="${ODOO_DB_HOST}" --port="${ODOO_DB_PORT}" --username="${ODOO_DB_USER}" --format=plain --no-owner --no-privileges "${ODOO_DB_NAME}" > "${DB_DUMP_FILE}"
echo "  -> Compressing filestore + database dump..."
WORK_DIR=$(mktemp -d)
trap "rm -rf ${WORK_DIR}" EXIT
mkdir -p "${WORK_DIR}/${TIMESTAMP}"
mv "${DB_DUMP_FILE}" "${WORK_DIR}/${TIMESTAMP}/database.sql"
[ -d "${ODOO_FILESTORE}/filestore" ] && cp -r "${ODOO_FILESTORE}/filestore" "${WORK_DIR}/${TIMESTAMP}/filestore"
[ -f "/etc/odoo/odoo.conf" ] && cp "/etc/odoo/odoo.conf" "${WORK_DIR}/${TIMESTAMP}/odoo.conf"
cat > "${WORK_DIR}/${TIMESTAMP}/MANIFEST" <<EOF
backup_date=${TIMESTAMP}
backup_type=${BACKUP_PREFIX}
odoo_db_name=${ODOO_DB_NAME}
EOF
tar -czf "${BACKUP_FILE}" -C "${WORK_DIR}" "${TIMESTAMP}"
echo "  -> Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "${BACKUP_PREFIX}_*.tar.gz" -mtime "+${RETENTION_DAYS}" -delete
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Backup complete: ${BACKUP_FILE}"
