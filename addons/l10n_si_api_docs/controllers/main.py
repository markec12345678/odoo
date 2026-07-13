# -*- coding: utf-8 -*-
"""Swagger UI controller — serves interactive API documentation.

Endpoints:
- GET /api/docs — Swagger UI HTML page
- GET /api/docs/openapi.yaml — raw OpenAPI 3.0 spec
"""
import os
import logging

from odoo import http
from odoo.http import Response

_logger = logging.getLogger(__name__)

# OpenAPI spec path relative to the Odoo addons path
# The spec lives in the main repo's docs/ directory
OPENAPI_SPEC_PATHS = [
    # Try multiple locations — spec may be in repo root or module
    os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'docs', 'openapi.yaml'),
    os.path.join(os.path.dirname(__file__), '..', 'static', 'openapi.yaml'),
    '/home/z/my-project/odoo/docs/openapi.yaml',
]

# Swagger UI HTML template (loaded from CDN)
SWAGGER_UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>SI/HR Tourism Suite — API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.11.0/swagger-ui.css">
    <style>
        html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
        *, *:before, *:after { box-sizing: inherit; }
        body { margin: 0; background: #fafafa; }
        .topbar { background: #1E3A5F; color: #fff; padding: 12px 24px; display: flex; align-items: center; gap: 16px; }
        .topbar h1 { font-size: 18px; margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
        .topbar a { color: #C8A951; text-decoration: none; font-size: 13px; }
        .topbar a:hover { text-decoration: underline; }
        .swagger-ui-wrap { max-width: 1200px; margin: 0 auto; padding: 20px; }
    </style>
</head>
<body>
    <div class="topbar">
        <h1>SI/HR Tourism Suite — API Documentation</h1>
        <a href="/healthz" target="_blank">Health Check</a>
        <a href="https://github.com/markec12345678/odoo" target="_blank">GitHub</a>
    </div>
    <div id="swagger-ui"></div>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.11.0/swagger-ui-bundle.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.11.0/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: '/api/docs/openapi.yaml',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: 'StandaloneLayout',
                validatorUrl: null,
                docExpansion: 'list',
                filter: true,
                showExtensions: true,
                showCommonExtensions: true,
            });
            window.ui = ui;
        };
    </script>
</body>
</html>"""


class ApiDocsController(http.Controller):
    """Swagger UI + OpenAPI spec endpoints."""

    @http.route('/api/docs', type='http', auth='none', methods=['GET'], csrf=False)
    def api_docs(self, **kwargs):
        """Serve Swagger UI HTML page."""
        return Response(
            SWAGGER_UI_HTML,
            status=200,
            content_type='text/html',
        )

    @http.route('/api/docs/openapi.yaml', type='http', auth='none', methods=['GET'], csrf=False)
    def api_docs_spec(self, **kwargs):
        """Serve the raw OpenAPI 3.0 YAML specification."""
        spec = self._load_openapi_spec()
        if spec:
            return Response(
                spec,
                status=200,
                content_type='application/yaml',
                headers={'Access-Control-Allow-Origin': '*'},
            )
        return Response(
            '# OpenAPI spec not found. Expected at docs/openapi.yaml',
            status=404,
            content_type='text/plain',
        )

    def _load_openapi_spec(self):
        """Load OpenAPI spec from one of the known paths."""
        for path in OPENAPI_SPEC_PATHS:
            try:
                path = os.path.normpath(path)
                if os.path.isfile(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        return f.read()
            except Exception as e:
                _logger.debug('OpenAPI spec not at %s: %s', path, e)
        _logger.warning('OpenAPI spec not found in any of: %s', OPENAPI_SPEC_PATHS)
        return None
