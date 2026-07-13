# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import logging
import os
import tempfile


from odoo import fields, models

_logger = logging.getLogger(__name__)

# FURS test/production endpoints for VAT existence check.
FURS_VAT_ENDPOINTS = {
    'test': 'https://blagajne-test.fu.gov.si:9002/v1/cash_registers/',
    'prod': 'https://blagajne.fu.gov.si:9002/v1/cash_registers/',
}


class ResCompany(models.Model):
    _inherit = 'res.company'

    si_vat_check_enabled = fields.Boolean(
        string='Check VAT with FURS',
        default=False,
        help='When enabled, the system validates VAT numbers against the FURS API. '
             'Requires a valid FURS certificate configured below.',
    )
    si_vat_endpoint = fields.Selection(
        selection=[('test', 'Test (blagajne-test.fu.gov.si)'),
                   ('prod', 'Production (blagajne.fu.gov.si)')],
        default='test',
        string='FURS Environment',
    )
    si_furs_certificate = fields.Binary(
        string='FURS Certificate (.p12)',
        help='PKCS12 file issued by FURS for API authentication.',
    )
    si_furs_certificate_filename = fields.Char(string='Certificate Filename')
    si_furs_certificate_password = fields.Char(
        string='Certificate Password',
        help='Password used when exporting the .p12 file. Stored in clear — '
             'use a dedicated FURS test cert for non-production environments.',
    )

    def _si_get_vat_endpoint(self):
        """Return the base URL for FURS VAT checks based on the company config."""
        self.ensure_one()
        return FURS_VAT_ENDPOINTS.get(self.si_vat_endpoint, FURS_VAT_ENDPOINTS['test'])

    def _si_get_cert_paths(self):
        """Materialize the configured .p12 to a temp file for `requests` to read.

        Returns (cert_path, key_path) or (None, None) if no certificate is set.
        The caller is responsible for deleting the temp files.
        """
        self.ensure_one()
        if not self.si_furs_certificate or not self.si_furs_certificate_password:
            return None, None

        p12_data = base64.b64decode(self.si_furs_certificate)
        tmpdir = tempfile.mkdtemp(prefix='furs_cert_')
        p12_path = os.path.join(tmpdir, 'furs.p12')

        with open(p12_path, 'wb') as f:
            f.write(p12_data)

        # Extract cert + key using openssl via subprocess (avoids pyOpenSSL version churn).
        cert_path = os.path.join(tmpdir, 'cert.pem')
        key_path = os.path.join(tmpdir, 'key.pem')

        import subprocess
        for cmd in (
            ['openssl', 'pkcs12', '-in', p12_path, '-out', cert_path, '-clcerts', '-nokeys',
             '-passin', f'pass:{self.si_furs_certificate_password}'],
            ['openssl', 'pkcs12', '-in', p12_path, '-out', key_path, '-nocerts',
             '-passin', f'pass:{self.si_furs_certificate_password}',
             '-passout', f'pass:{self.si_furs_certificate_password}'],
        ):
            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=10)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                _logger.warning('FURS cert extraction failed: %s', e)
                return None, None
        # Strip the encryption on the key (requests does not support encrypted keys directly).
        try:
            subprocess.run(
                ['openssl', 'rsa', '-in', key_path, '-out', key_path,
                 '-passin', f'pass:{self.si_furs_certificate_password}'],
                check=True, capture_output=True, timeout=10,
            )
        except subprocess.CalledProcessError as e:
            _logger.warning('FURS key decryption failed: %s', e)
            return None, None

        return cert_path, key_path
