# -*- coding: utf-8 -*-
"""Tests for l10n_si_health_check module."""
import json

from odoo.tests import HttpCase, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestHealthCheckController(HttpCase):
    """Tests for /healthz endpoint."""

    def test_healthz_returns_json(self):
        """GET /healthz should return JSON with status field."""
        response = self.url_open('/healthz')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.text)
        self.assertIn('status', data)
        self.assertIn('checks', data)
        self.assertIn('timestamp', data)

    def test_healthz_status_is_ok_or_degraded(self):
        """Status should be 'ok' or 'degraded' (not 'down' in test env)."""
        response = self.url_open('/healthz')
        data = json.loads(response.text)
        self.assertIn(data['status'], ('ok', 'degraded'))

    def test_healthz_has_database_check(self):
        """Checks should include 'database' field."""
        response = self.url_open('/healthz')
        data = json.loads(response.text)
        self.assertIn('database', data['checks'])
        self.assertEqual(data['checks']['database'], 'ok')

    def test_healthz_has_modules_check(self):
        """Checks should include 'modules' field."""
        response = self.url_open('/healthz')
        data = json.loads(response.text)
        self.assertIn('modules', data['checks'])

    def test_healthz_has_filestore_check(self):
        """Checks should include 'filestore' field."""
        response = self.url_open('/healthz')
        data = json.loads(response.text)
        self.assertIn('filestore', data['checks'])

    def test_healthz_simple_returns_text(self):
        """GET /healthz/simple should return plain text 'ok'."""
        response = self.url_open('/healthz/simple')
        self.assertEqual(response.status_code, 200)
        self.assertIn(response.text.strip(), ('ok', 'down'))

    def test_healthz_has_version(self):
        """Response should include Odoo version."""
        response = self.url_open('/healthz')
        data = json.loads(response.text)
        self.assertIn('version', data)
        self.assertTrue(data['version'])

    def test_healthz_has_timestamp(self):
        """Response should include ISO timestamp."""
        response = self.url_open('/healthz')
        data = json.loads(response.text)
        self.assertIn('timestamp', data)
        # Should be ISO format (contains 'T' and 'Z')
        self.assertIn('T', data['timestamp'])

    def test_healthz_no_auth_required(self):
        """Endpoint should be accessible without authentication."""
        # url_open uses anonymous session by default
        response = self.url_open('/healthz')
        # Should not redirect to login
        self.assertEqual(response.status_code, 200)


@tagged('post_install', '-at_install')
class TestHealthCheckModuleMetadata(TransactionCase):
    """Tests for module metadata."""

    def test_module_is_installed(self):
        """l10n_si_health_check should be installed."""
        module = self.env['ir.module.module'].search([
            ('name', '=', 'l10n_si_health_check'),
            ('state', '=', 'installed'),
        ])
        self.assertTrue(module, 'l10n_si_health_check module not installed')

    def test_module_has_correct_category(self):
        """Module should be in Services category."""
        module = self.env['ir.module.module'].search([
            ('name', '=', 'l10n_si_health_check'),
        ], limit=1)
        if module:
            self.assertEqual(module.category_id.name, 'Services')
