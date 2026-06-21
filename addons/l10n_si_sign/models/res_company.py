# -*- coding: utf-8 -*-
import base64
import logging
import os
import shutil
import subprocess
import tempfile

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)

# Free SI-TRUST TSA (RFC 3161 timestamp)
DEFAULT_TSA_URL = 'https://tsa.si-trust.gov.si'


class ResCompany(models.Model):
    _inherit = 'res.company'

    si_sign_certificate = fields.Binary(
        string='eIDAS Certificate (.p12)',
        help='Qualified certificate from SI-TRUST / CA HALCOM / SIGEN-CA.',
    )
    si_sign_certificate_filename = fields.Char(string='Certificate Filename')
    si_sign_certificate_password = fields.Char(string='Certificate Password')
    si_sign_tsa_url = fields.Char(
        string='TSA URL',
        default=DEFAULT_TSA_URL,
        help='Trusted timestamp authority. Default: SI-TRUST free TSA.',
    )
    si_sign_default_workflow = fields.Selection(
        selection=[('parallel', 'Vzporedno (vsi hkrati)'),
                   ('sequential', 'Zaporedno (po vrsti)')],
        default='sequential',
        string='Privzeti potek podpisov',
    )

    def si_sign_get_cert_paths(self):
        """Extract PEM cert + key from the .p12 eIDAS cert.

        Returns (cert_path, key_path, temp_dir) for use with external tools.
        Caller must shutil.rmtree(temp_dir) when done.
        """
        self.ensure_one()
        if not self.si_sign_certificate or not self.si_sign_certificate_password:
            return None, None, None

        p12_data = base64.b64decode(self.si_sign_certificate)
        temp_dir = tempfile.mkdtemp(prefix='eidas_sign_')
        p12_path = os.path.join(temp_dir, 'cert.p12')
        cert_path = os.path.join(temp_dir, 'cert.pem')
        key_path = os.path.join(temp_dir, 'key.pem')

        with open(p12_path, 'wb') as f:
            f.write(p12_data)

        cmds = [
            ['openssl', 'pkcs12', '-in', p12_path, '-out', cert_path, '-clcerts', '-nokeys',
             '-passin', f'pass:{self.si_sign_certificate_password}'],
            ['openssl', 'pkcs12', '-in', p12_path, '-out', key_path, '-nocerts',
             '-passin', f'pass:{self.si_sign_certificate_password}',
             '-passout', f'pass:{self.si_sign_certificate_password}'],
            ['openssl', 'rsa', '-in', key_path, '-out', key_path,
             '-passin', f'pass:{self.si_sign_certificate_password}'],
        ]
        for cmd in cmds:
            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=10)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                _logger.warning('eIDAS cert extraction failed: %s', e)
                shutil.rmtree(temp_dir, ignore_errors=True)
                return None, None, None
        return cert_path, key_path, temp_dir

    @api.constrains('si_sign_certificate', 'si_sign_certificate_password')
    def _check_sign_cert(self):
        for company in self:
            if company.si_sign_certificate and not company.si_sign_certificate_password:
                raise exceptions.ValidationError(_('Certificate password is required.'))
