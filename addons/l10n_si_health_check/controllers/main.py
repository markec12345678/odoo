# -*- coding: utf-8 -*-
"""Health check endpoint for Railway / load balancer monitoring.

GET /healthz — returns JSON with overall status + component checks.

Checks:
1. Database connection (SELECT 1)
2. Critical modules installed
3. Filestore writable

Response codes:
- 200: status = "ok" or "degraded"
- 503: status = "down" (database unreachable)
"""
import json
import logging
import os
import time

from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

# Modules that should be installed for full functionality.
# If any are missing, status is "degraded" (not "down").
CRITICAL_MODULES = [
    'l10n_si_fiscal',
    'l10n_si_etourism',
    'l10n_si_hotel',
    'l10n_hr_fiscal',
    'l10n_hr_evisitor',
]

IMPORTANT_MODULES = [
    'l10n_si_ai_concierge',
    'l10n_si_whatsapp_business',
    'l10n_si_channel_manager',
    'l10n_si_pos_advanced',
    'l10n_si_restaurant',
    'l10n_si_wellness',
]


class HealthCheckController(http.Controller):
    """Public health check endpoint — no authentication required."""

    @http.route('/healthz', type='http', auth='none', methods=['GET'], csrf=False)
    def healthz(self, **kwargs):
        """Return health status as JSON."""
        checks = {}
        overall_status = 'ok'

        # 1. Database check
        checks['database'] = self._check_database()
        if checks['database'] != 'ok':
            overall_status = 'down'

        # 2. Critical modules check
        if overall_status != 'down':
            checks['modules'] = self._check_modules()
            if 'missing' in checks['modules']:
                overall_status = 'degraded'

        # 3. Filestore check
        if overall_status != 'down':
            checks['filestore'] = self._check_filestore()
            if checks['filestore'] != 'ok':
                overall_status = 'degraded'

        # 4. Backup check (informational — doesn't affect overall status)
        if overall_status != 'down':
            checks['backup'] = self._check_backup()

        # 5. Uptime
        checks['uptime_seconds'] = int(time.time() - self._get_start_time())

        result = {
            'status': overall_status,
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'checks': checks,
            'version': self._get_odoo_version(),
            'database': self._get_db_name(),
            'api_docs': '/api/docs',
        }

        status_code = 200 if overall_status != 'down' else 503
        return Response(
            json.dumps(result, indent=2),
            status=status_code,
            content_type='application/json',
        )

    @http.route('/healthz/simple', type='http', auth='none', methods=['GET'], csrf=False)
    def healthz_simple(self, **kwargs):
        """Simple text endpoint — returns 'ok' or 'down'.

        Use this for Railway healthcheck (simpler parsing).
        """
        db_status = self._check_database()
        if db_status == 'ok':
            return Response('ok', status=200, content_type='text/plain')
        return Response('down', status=503, content_type='text/plain')

    def _check_database(self):
        """Check if database is accessible."""
        try:
            request.env.cr.execute('SELECT 1')
            result = request.env.cr.fetchone()
            if result and result[0] == 1:
                return 'ok'
            return 'error: unexpected response'
        except Exception as e:
            _logger.error('Health check: database error: %s', e)
            return f'error: {str(e)[:200]}'

    def _check_modules(self):
        """Check if critical modules are installed."""
        try:
            Module = request.env['ir.module.module']
            installed = Module.search([
                ('name', 'in', CRITICAL_MODULES + IMPORTANT_MODULES),
                ('state', '=', 'installed'),
            ])
            installed_names = set(installed.mapped('name'))

            missing_critical = [
                m for m in CRITICAL_MODULES if m not in installed_names
            ]
            missing_important = [
                m for m in IMPORTANT_MODULES if m not in installed_names
            ]

            parts = [f'{len(installed_names)}/{len(CRITICAL_MODULES) + len(IMPORTANT_MODULES)} installed']
            if missing_critical:
                parts.append(f'missing critical: {", ".join(missing_critical)}')
            if missing_important:
                parts.append(f'missing important: {", ".join(missing_important)}')
            return '; '.join(parts)
        except Exception as e:
            _logger.error('Health check: module check error: %s', e)
            return f'error: {str(e)[:200]}'

    def _check_filestore(self):
        """Check if filestore directory is writable."""
        try:
            filestore_dir = os.path.join(
                request.env['ir.attachment']._filestore(),
            )
            test_file = os.path.join(filestore_dir, '.healthcheck')
            with open(test_file, 'w') as f:
                f.write('ok')
            os.remove(test_file)
            return 'ok'
        except Exception as e:
            _logger.error('Health check: filestore error: %s', e)
            return f'error: {str(e)[:200]}'

    def _check_backup(self):
        """Check backup status — looks for recent backup files.

        Returns:
        - 'ok: <timestamp> (<size>)' if backup < 25 hours old
        - 'stale: last backup <timestamp> (>25h ago)' if backup exists but old
        - 'no backup found' if no backup files exist
        - 'error: <message>' on errors
        """
        import glob
        from datetime import datetime

        backup_dirs = [
            '/tmp/backups',
            os.environ.get('BACKUP_DIR', '/tmp/backups'),
        ]
        backup_prefix = os.environ.get('BACKUP_PREFIX', 'daily')

        latest_file = None
        latest_mtime = 0

        for backup_dir in backup_dirs:
            if not os.path.isdir(backup_dir):
                continue
            pattern = os.path.join(backup_dir, f'{backup_prefix}_*.tar.gz')
            for fpath in glob.glob(pattern):
                mtime = os.path.getmtime(fpath)
                if mtime > latest_mtime:
                    latest_mtime = mtime
                    latest_file = fpath

        if not latest_file:
            return 'no backup found'

        # Check age
        backup_time = datetime.fromtimestamp(latest_mtime)
        now = datetime.now()
        age_hours = (now - backup_time).total_seconds() / 3600

        file_size = os.path.getsize(latest_file)
        if file_size > 1024 * 1024:
            size_str = f'{file_size / (1024 * 1024):.1f} MB'
        else:
            size_str = f'{file_size / 1024:.0f} KB'

        timestamp_str = backup_time.strftime('%Y-%m-%d %H:%M UTC')

        if age_hours > 25:
            return f'stale: last backup {timestamp_str} ({age_hours:.0f}h ago, {size_str})'
        return f'ok: {timestamp_str} ({size_str}, {age_hours:.1f}h ago)'


    def _get_odoo_version(self):
        """Get Odoo version string."""
        try:
            import odoo
            return odoo.release.version
        except Exception:
            return 'unknown'

    def _get_db_name(self):
        """Get current database name."""
        try:
            return request.env.cr.dbname
        except Exception:
            return 'unknown'

    def _get_start_time(self):
        """Get approximate server start time (for uptime calculation)."""
        # Odoo doesn't expose start time directly; use process start time
        try:
            import psutil
            return psutil.Process(os.getpid()).create_time()
        except ImportError:
            # Fallback: use current time (uptime will show 0)
            return time.time()
