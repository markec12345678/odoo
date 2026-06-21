# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import logging
import os
import tempfile

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)

FURS_ENDPOINTS = {
    'test': 'https://blagajne-test.fu.gov.si:9002/v1/cash_registers/',
    'prod': 'https://blagajne.fu.gov.si:9002/v1/cash_registers/',
}


class ResCompany(models.Model):
    _inherit = 'res.company'

    si_fiscal_enabled = fields.Boolean(
        string='Fiscal Verification Enabled',
        default=True,
        help='When enabled, all cash invoices will be submitted to FURS for ZOI/EOR.',
    )
    si_fiscal_environment = fields.Selection(
        selection=[('test', 'Test'),
                   ('prod', 'Production')],
        default='test',
        string='FURS Environment',
        required=True,
    )
    si_fiscal_auto_submit = fields.Boolean(
        string='Auto-submit to FURS',
        default=True,
        help='When True, invoices are submitted immediately on posting. '
             'When False, you must run the action_si_submit_to_furs manually.',
    )
    si_fiscal_certificate = fields.Binary(
        string='FURS Certificate (.p12)',
        help='PKCS12 certificate issued by FURS for API authentication.',
    )
    si_fiscal_certificate_filename = fields.Char(string='Certificate Filename')
    si_fiscal_certificate_password = fields.Char(
        string='Certificate Password',
        help='Password protecting the .p12 file. Stored in clear — protect at OS level.',
    )
    si_fiscal_software_supplier_tax_no = fields.Char(
        string='Software Supplier Tax Number',
        help='Tax number of the company that developed/maintains this Odoo instance. '
             'If you self-host, this is your own tax number.',
    )

    def si_fiscal_get_endpoint(self):
        self.ensure_one()
        return FURS_ENDPOINTS.get(self.si_fiscal_environment, FURS_ENDPOINTS['test'])

    def si_fiscal_get_cert_paths(self):
        """Materialize the .p12 to PEM cert + key files for `requests`.

        Returns (cert_path, key_path, temp_dir). Caller must shutil.rmtree(temp_dir).
        Returns (None, None, None) if cert is not configured.
        """
        self.ensure_one()
        if not self.si_fiscal_certificate or not self.si_fiscal_certificate_password:
            return None, None, None

        import subprocess

        p12_data = base64.b64decode(self.si_fiscal_certificate)
        temp_dir = tempfile.mkdtemp(prefix='furs_fiscal_')
        p12_path = os.path.join(temp_dir, 'cert.p12')
        cert_path = os.path.join(temp_dir, 'cert.pem')
        key_path = os.path.join(temp_dir, 'key.pem')

        with open(p12_path, 'wb') as f:
            f.write(p12_data)

        cmds = [
            (['openssl', 'pkcs12', '-in', p12_path, '-out', cert_path, '-clcerts', '-nokeys',
              '-passin', f'pass:{self.si_fiscal_certificate_password}'], 'cert extract'),
            (['openssl', 'pkcs12', '-in', p12_path, '-out', key_path, '-nocerts',
              '-passin', f'pass:{self.si_fiscal_certificate_password}',
              '-passout', f'pass:{self.si_fiscal_certificate_password}'], 'key extract'),
            (['openssl', 'rsa', '-in', key_path, '-out', key_path,
              '-passin', f'pass:{self.si_fiscal_certificate_password}'], 'key decrypt'),
        ]
        for cmd, label in cmds:
            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=10)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                _logger.warning('FURS %s failed: %s', label, e)
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                return None, None, None

        return cert_path, key_path, temp_dir

    @api.constrains('si_fiscal_enabled', 'si_fiscal_certificate')
    def _check_fiscal_cert_configured(self):
        for company in self:
            if company.si_fiscal_enabled and not company.si_fiscal_certificate:
                raise exceptions.ValidationError(_(
                    'Fiscal verification is enabled but no FURS certificate is configured. '
                    'Upload the .p12 certificate in the Fiscal tab.'
                ))
