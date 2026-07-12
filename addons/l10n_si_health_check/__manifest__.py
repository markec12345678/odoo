# -*- coding: utf-8 -*-
{
    'name': 'SI/HR Health Check Endpoint',
    'summary': 'Production health check — DB, modules, config verification',
    'version': '19.0.1.0.0',
    'category': 'Services',
    'description': """
SI/HR Health Check Endpoint
============================

Production health check endpoint for Railway/load balancer monitoring.

Endpoint: GET /healthz
Returns: JSON with overall status + component checks

Checks performed:
1. Database connection (SELECT 1)
2. Critical modules installed (l10n_si_fiscal, l10n_hr_fiscal, etc.)
3. Odoo server responding
4. Memory/filestore accessible

Usage:
- Railway healthcheck: set to /healthz
- Load balancer: poll /healthz every 30s
- Monitoring: alert if status != "ok"

Response format:
{
  "status": "ok" | "degraded" | "down",
  "timestamp": "2026-07-13T10:00:00Z",
  "checks": {
    "database": "ok",
    "modules": "ok",
    "filestore": "ok"
  },
  "version": "19.0.14.3",
  "modules_checked": 5
}
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
}
