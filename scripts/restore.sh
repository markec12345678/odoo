#!/usr/bin/env bash
# Slovenian Odoo restore script.
set -euo pipefail
[ $# -lt 1 ] && { echo "Usage: $0 <backup_file.tar.gz>"; exit 1; }
BACKUP_FILE="$1"
[ ! -f "${BACKUP_FILE}" ] && { echo "ERROR: Backup file not found: ${BACKUP_FILE}"; exit 1; }
ODOO_DB_NAME="${ODOO_DB_NAME:-si_odoo}"
ODOO_DB_USER="${ODOO_DB_USER:-odoo}"
ODOO_DB_HOST="${ODOO_DB_HOST:-db}"
ODOO_DB_PORT="${ODOO_DB_PORT:-5432}"
ODOO_FILESTORE="${ODOO_FILESTORE:-/var/lib/odoo}"
WORK_DIR=$(mktemp -d)
trap "rm -rf ${WORK_DIR}" EXIT
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Restoring from ${BACKUP_FILE}"
tar -xzf "${BACKUP_FILE}" -C "${WORK_DIR}"
RESTORE_DIR=$(find "${WORK_DIR}" -maxdepth 1 -type d -name "20*" | head -1)
[ -z "${RESTORE_DIR}" ] && { echo "ERROR: Could not find restore directory."; exit 1; }
if [ -f "${RESTORE_DIR}/database.sql" ]; then
    echo "  -> Restoring database '${ODOO_DB_NAME}'..."
    PGPASSWORD="${PGPASSWORD:-}" psql --host="${ODOO_DB_HOST}" --port="${ODOO_DB_PORT}" --username="${ODOO_DB_USER}" --dbname=postgres --command="DROP DATABASE IF EXISTS \"${ODOO_DB_NAME}\";"
    PGPASSWORD="${PGPASSWORD:-}" psql --host="${ODOO_DB_HOST}" --port="${ODOO_DB_PORT}" --username="${ODOO_DB_USER}" --dbname=postgres --command="CREATE DATABASE \"${ODOO_DB_NAME}\" OWNER \"${ODOO_DB_USER}\";"
    PGPASSWORD="${PGPASSWORD:-}" psql --host="${ODOO_DB_HOST}" --port="${ODOO_DB_PORT}" --username="${ODOO_DB_USER}" --dbname="${ODOO_DB_NAME}" --file="${RESTORE_DIR}/database.sql"
    echo "    Database restored."
fi
if [ -d "${RESTORE_DIR}/filestore" ]; then
    echo "  -> Restoring filestore..."
    mkdir -p "${ODOO_FILESTORE}"
    rm -rf "${ODOO_FILESTORE}/filestore"
    cp -r "${RESTORE_DIR}/filestore" "${ODOO_FILESTORE}/filestore"
    chown -R odoo:odoo "${ODOO_FILESTORE}/filestore" 2>/dev/null || true
    echo "    Filestore restored."
fi
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Restore complete."
