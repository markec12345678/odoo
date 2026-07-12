# -*- coding: utf-8 -*-
{
    'name': 'SI/HR API Documentation (Swagger UI)',
    'summary': 'Interaktivna API dokumentacija — Swagger UI z OpenAPI 3.0 spec',
    'version': '19.0.1.0.0',
    'category': 'Services',
    'description': """
SI/HR API Documentation (Swagger UI)
=====================================

Serves interactive API documentation at /api/docs using Swagger UI.

Loads the OpenAPI 3.0 specification from docs/openapi.yaml and renders
it with Swagger UI (loaded from CDN — no npm dependencies).

Endpoints:
- GET /api/docs — Swagger UI HTML page
- GET /api/docs/openapi.yaml — raw OpenAPI spec (for external tools)

Usage:
- Browse to https://your-domain/api/docs
- Try API calls directly from the browser
- Import /api/docs/openapi.yaml into Postman, Insomnia, etc.
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
