# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import logging
import os
import shutil
import subprocess
import tempfile

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)

FURS_EDAVKI_ENDPOINTS = {
    'test': 'https://edavki-test.fu.gov.si/ERacunAPI/api/eracun',
    'prod': 'https://edavki.fu.gov.si/ERacunAPI/api/eracun',
}


class ResCompany(models.Model):
    _inherit = 'res.company'

    si_edi_enabled = fields.Boolean(
        string='e-Račun (eSLOG 2.0) Enabled',
        default=False,
        help='When enabled, posted invoices are converted to eSLOG 2.0 XML and '
             'submitted to FURS eDavki.',
    )
    si_edi_environment = fields.Selection(
        selection=[('test', 'Test (edavki-test.fu.gov.si)'),
                   ('prod', 'Production (edavki.fu.gov.si)')],
        default='test',
        string='eDavki Environment',
        required=True,
    )
    si_edi_certificate = fields.Binary(
        string='eIDAS Certificate (.p12)',
        help='Qualified certificate from SI-TRUST, CA HALCOM, or SIGEN-CA. '
             'Required for B2B/B2G e-invoice signing.',
    )
    si_edi_certificate_filename = fields.Char(string='Certificate Filename')
    si_edi_certificate_password = fields.Char(string='Certificate Password')
    si_edi_peppol_id = fields.Char(
        string='PEPPOL Identifier',
        help='Default: SI + 8-digit tax number (e.g. SI12345678).',
    )
    si_edi_auto_submit = fields.Boolean(
        string='Auto-submit on posting',
        default=False,
        help='If True, eSLOG XML is generated and submitted automatically when '
             'an invoice is posted. If False, run action_si_edi_submit manually.',
    )

    def si_edi_get_endpoint(self):
        self.ensure_one()
        return FURS_EDAVKI_ENDPOINTS.get(self.si_edi_environment, FURS_EDAVKI_ENDPOINTS['test'])

    def si_edi_get_cert_paths(self):
        """Extract cert + key PEMs from the .p12 eIDAS certificate."""
        self.ensure_one()
        if not self.si_edi_certificate or not self.si_edi_certificate_password:
            return None, None, None

        p12_data = base64.b64decode(self.si_edi_certificate)
        temp_dir = tempfile.mkdtemp(prefix='eidas_')
        p12_path = os.path.join(temp_dir, 'cert.p12')
        cert_path = os.path.join(temp_dir, 'cert.pem')
        key_path = os.path.join(temp_dir, 'key.pem')

        with open(p12_path, 'wb') as f:
            f.write(p12_data)

        cmds = [
            ['openssl', 'pkcs12', '-in', p12_path, '-out', cert_path, '-clcerts', '-nokeys',
             '-passin', f'pass:{self.si_edi_certificate_password}'],
            ['openssl', 'pkcs12', '-in', p12_path, '-out', key_path, '-nocerts',
             '-passin', f'pass:{self.si_edi_certificate_password}',
             '-passout', f'pass:{self.si_edi_certificate_password}'],
            ['openssl', 'rsa', '-in', key_path, '-out', key_path,
             '-passin', f'pass:{self.si_edi_certificate_password}'],
        ]
        for cmd in cmds:
            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=10)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                _logger.warning('eIDAS cert extraction failed: %s', e)
                shutil.rmtree(temp_dir, ignore_errors=True)
                return None, None, None
        return cert_path, key_path, temp_dir

    @api.constrains('si_edi_enabled', 'si_edi_certificate', 'si_edi_peppol_id')
    def _check_edi_config(self):
        for company in self:
            if company.si_edi_enabled:
                if not company.si_edi_certificate:
                    raise exceptions.ValidationError(_(
                        'e-Račun is enabled but no eIDAS certificate is configured.',
                    ))
                if not company.si_edi_peppol_id:
                    raise exceptions.ValidationError(_(
                        'PEPPOL identifier is required for e-Račun. '
                        'Format: SI + 8-digit tax number.',
                    ))
