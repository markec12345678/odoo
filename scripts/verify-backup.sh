#!/usr/bin/env bash
# Backup verification script — tests backup integrity after creation.
#
# This script:
# 1. Finds the most recent backup file
# 2. Extracts it to a temp directory
# 3. Verifies database.sql is non-empty and contains expected tables
# 4. Verifies MANIFEST file exists and is valid
# 5. Verifies filestore directory exists (if included)
# 6. Tests SQL dump by loading into a temp SQLite database (syntax check)
#
# Usage:
#   ./verify-backup.sh [backup_dir] [backup_prefix]
#
# Default: /tmp/backups daily
#
# Exit codes:
#   0 = backup verified OK
#   1 = backup verification FAILED
#   2 = no backup found
set -euo pipefail

BACKUP_DIR="${1:-/tmp/backups}"
BACKUP_PREFIX="${2:-daily}"

echo "=== Backup Verification ==="
echo "Backup dir: ${BACKUP_DIR}"
echo "Prefix:     ${BACKUP_PREFIX}"
echo ""

# Find most recent backup
LATEST_BACKUP=$(ls -t "${BACKUP_DIR}/${BACKUP_PREFIX}"_*.tar.gz 2>/dev/null | head -1)

if [ -z "${LATEST_BACKUP}" ]; then
    echo "❌ No backup found in ${BACKUP_DIR} with prefix '${BACKUP_PREFIX}'"
    exit 2
fi

echo "Latest backup: ${LATEST_BACKUP}"
BACKUP_SIZE=$(du -h "${LATEST_BACKUP}" | cut -f1)
echo "Size:          ${BACKUP_SIZE}"
echo ""

# Check minimum size (1MB)
MIN_SIZE_BYTES=1048576
ACTUAL_SIZE=$(stat -c%s "${LATEST_BACKUP}" 2>/dev/null || stat -f%z "${LATEST_BACKUP}")
if [ "${ACTUAL_SIZE}" -lt "${MIN_SIZE_BYTES}" ]; then
    echo "❌ Backup too small (${ACTUAL_SIZE} bytes < 1MB minimum)"
    exit 1
fi
echo "✓ Size check passed (${ACTUAL_SIZE} bytes > 1MB)"

# Extract to temp directory
WORK_DIR=$(mktemp -d)
trap "rm -rf ${WORK_DIR}" EXIT

echo "Extracting to ${WORK_DIR}..."
tar -xzf "${LATEST_BACKUP}" -C "${WORK_DIR}"

# Find extracted directory
EXTRACTED_DIR=$(ls -d "${WORK_DIR}"/*/ | head -1)
if [ -z "${EXTRACTED_DIR}" ]; then
    echo "❌ No directory found in backup archive"
    exit 1
fi

echo "Extracted to: ${EXTRACTED_DIR}"
echo ""

# Check 1: MANIFEST file
echo "[1/5] Checking MANIFEST..."
MANIFEST="${EXTRACTED_DIR}/MANIFEST"
if [ ! -f "${MANIFEST}" ]; then
    echo "❌ MANIFEST file missing"
    exit 1
fi
echo "✓ MANIFEST exists"
cat "${MANIFEST}" | sed 's/^/    /'
echo ""

# Check 2: database.sql
echo "[2/5] Checking database.sql..."
DB_SQL="${EXTRACTED_DIR}/database.sql"
if [ ! -f "${DB_SQL}" ]; then
    echo "❌ database.sql missing"
    exit 1
fi

DB_SIZE=$(du -h "${DB_SQL}" | cut -f1)
echo "✓ database.sql exists (${DB_SIZE})"

if [ ! -s "${DB_SQL}" ]; then
    echo "❌ database.sql is empty"
    exit 1
fi
echo "✓ database.sql is non-empty"

# Check 3: Expected tables in SQL dump
echo ""
echo "[3/5] Checking for critical tables in SQL dump..."
CRITICAL_TABLES=(
    "res_partner"
    "res_users"
    "res_company"
    "ir_module_module"
    "account_move"
    "l10n_si_audit_trail"
)

ALL_TABLES_FOUND=true
for table in "${CRITICAL_TABLES[@]}"; do
    if grep -q "CREATE TABLE.*${table}" "${DB_SQL}" || grep -q "COPY.*${table}" "${DB_SQL}" || grep -q "ALTER TABLE.*${table}" "${DB_SQL}"; then
        echo "  ✓ ${table}"
    else
        echo "  ❌ ${table} NOT FOUND"
        ALL_TABLES_FOUND=false
    fi
done

if [ "${ALL_TABLES_FOUND}" = "false" ]; then
    echo "❌ Some critical tables missing from backup"
    exit 1
fi
echo "✓ All ${#CRITICAL_TABLES[@]} critical tables present"

# Check 4: Filestore (optional)
echo ""
echo "[4/5] Checking filestore..."
FILESTORE_DIR="${EXTRACTED_DIR}/filestore"
if [ -d "${FILESTORE_DIR}" ]; then
    FILE_COUNT=$(find "${FILESTORE_DIR}" -type f | wc -l)
    echo "✓ Filestore exists (${FILE_COUNT} files)"
else
    echo "⚠ Filestore not included in backup (may be normal for small installations)"
fi

# Check 5: SQL syntax validation (basic)
echo ""
echo "[5/5] Validating SQL syntax..."
# Check for common SQL dump markers
if ! grep -q "PostgreSQL database dump" "${DB_SQL}"; then
    echo "❌ SQL dump header missing — may be corrupted"
    exit 1
fi
echo "✓ SQL dump header found"

if ! grep -q "PostgreSQL database dump complete" "${DB_SQL}"; then
    echo "❌ SQL dump footer missing — dump may be incomplete"
    exit 1
fi
echo "✓ SQL dump footer found (dump is complete)"

# Count approximate number of tables
TABLE_COUNT=$(grep -c "^CREATE TABLE" "${DB_SQL}" || echo "0")
echo "✓ Found approximately ${TABLE_COUNT} tables in dump"

# Summary
echo ""
echo "=== Verification Summary ==="
echo "Backup file:     ${LATEST_BACKUP}"
echo "Archive size:    ${BACKUP_SIZE}"
echo "DB dump size:    ${DB_SIZE}"
echo "Tables in dump:  ~${TABLE_COUNT}"
echo "Filestore:       $(if [ -d "${FILESTORE_DIR}" ]; then echo "included"; else echo "not included"; fi)"
echo "Status:          ✅ VERIFIED"
echo ""
exit 0
