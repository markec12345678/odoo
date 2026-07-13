# -*- coding: utf-8 -*-
"""Bank sync configuration — one record per bank account."""
import base64
import logging
import os
import shutil
import subprocess
import tempfile
from datetime import date, timedelta

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

BANK_API_ENDPOINTS = {
    'nlb': {
        'test': 'https://poslovnibanka-test.nlb.si/api/v2/statements',
        'prod': 'https://poslovnibanka.nlb.si/api/v2/statements',
    },
    'nkbm': {
        'test': 'https://ebank-test.nkbm.si/api/v1/statements',
        'prod': 'https://ebank.nkbm.si/api/v1/statements',
    },
    'sparkasse': {
        'test': 'https://george-test.sparkasse.si/api/v3/statements',
        'prod': 'https://george.sparkasse.si/api/v3/statements',
    },
    'addiko': {
        'test': 'https://api-test.addiko.si/v1/statements',
        'prod': 'https://api.addiko.si/v1/statements',
    },
    'raiffeisen': {
        'test': 'https://ebanka-test.rba.si/api/statements',
        'prod': 'https://ebanka.rba.si/api/statements',
    },
}


class L10nSiBankSyncConfig(models.Model):
    _name = 'l10n_si.bank.sync.config'
    _description = 'Slovenian Bank Sync Configuration'
    _order = 'bank_code, iban'

    name = fields.Char(compute='_compute_name', store=True)
    bank_code = fields.Selection(
        selection=[('nlb', 'NLB'),
                   ('nkbm', 'NKBM'),
                   ('sparkasse', 'Sparkasse'),
                   ('addiko', 'Addiko'),
                   ('raiffeisen', 'Raiffeisen')],
        required=True,
    )
    iban = fields.Char(required=True, size=34)
    journal_id = fields.Many2one('account.journal', required=True, ondelete='restrict')
    company_id = fields.Many2one(
        'res.company', related='journal_id.company_id', store=True,
    )
    environment = fields.Selection(
        selection=[('test', 'Test'), ('prod', 'Produkcija')],
        default='test', required=True,
    )
    api_username = fields.Char(string='API uporabnik')
    api_password = fields.Char(string='API geslo')
    api_key = fields.Char(string='API ključ')
    certificate = fields.Binary(string='Certifikat (.p12)')
    certificate_filename = fields.Char()
    certificate_password = fields.Char(string='Certifikat geslo')
    oauth_client_id = fields.Char(string='OAuth client ID')
    oauth_client_secret = fields.Char(string='OAuth client secret')
    oauth_token = fields.Text(readonly=True, copy=False)
    oauth_token_expires_at = fields.Datetime(readonly=True, copy=False)

    auto_sync = fields.Boolean(default=True)
    last_sync_date = fields.Datetime(readonly=True, copy=False)
    log_ids = fields.One2many('l10n_si.bank.sync.log', 'config_id', string='Sync Logs')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('iban_company_uniq', 'unique(iban, company_id)',
         'IBAN must be unique per company.'),
    ]

    @api.depends('bank_code', 'iban')
    def _compute_name(self):
        for cfg in self:
            cfg.name = f'{cfg.bank_code.upper()} - {cfg.iban or ""}'

    def _get_endpoint(self):
        self.ensure_one()
        return BANK_API_ENDPOINTS[self.bank_code][self.environment]

    def _get_cert_paths(self):
        """Extract cert + key PEMs from .p12."""
        self.ensure_one()
        if not self.certificate or not self.certificate_password:
            return None, None, None
        p12_data = base64.b64decode(self.certificate)
        temp_dir = tempfile.mkdtemp(prefix=f'bank_sync_{self.bank_code}_')
        p12_path = os.path.join(temp_dir, 'cert.p12')
        cert_path = os.path.join(temp_dir, 'cert.pem')
        key_path = os.path.join(temp_dir, 'key.pem')
        with open(p12_path, 'wb') as f:
            f.write(p12_data)
        cmds = [
            ['openssl', 'pkcs12', '-in', p12_path, '-out', cert_path, '-clcerts', '-nokeys',
             '-passin', f'pass:{self.certificate_password}'],
            ['openssl', 'pkcs12', '-in', p12_path, '-out', key_path, '-nocerts',
             '-passin', f'pass:{self.certificate_password}',
             '-passout', f'pass:{self.certificate_password}'],
            ['openssl', 'rsa', '-in', key_path, '-out', key_path,
             '-passin', f'pass:{self.certificate_password}'],
        ]
        for cmd in cmds:
            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=10)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                shutil.rmtree(temp_dir, ignore_errors=True)
                return None, None, None
        return cert_path, key_path, temp_dir

    def action_test_connection(self):
        """Verify that credentials + cert work against the bank API."""
        for cfg in self:
            try:
                cfg._fetch_statements(date.today() - timedelta(days=1), date.today())
                cfg.message_post(body=_('Connection test successful.')) if hasattr(cfg, 'message_post') else None
            except Exception as e:  # noqa: BLE001
                raise UserError(_('Connection test failed: %s') % e) from e
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Connection test passed for all selected configs.'),
                'type': 'success',
            },
        }

    def action_sync_now(self):
        """Manual sync — fetch yesterday's statements."""
        for cfg in self:
            cfg._sync_one_day(date.today() - timedelta(days=1))

    def _sync_one_day(self, target_date):
        """Fetch and import statements for a single date."""
        self.ensure_one()
        log = self.env['l10n_si.bank.sync.log'].create({
            'config_id': self.id,
            'company_id': self.company_id.id,
            'date_from': target_date,
            'date_to': target_date,
            'state': 'pending',
        })
        try:
            xml_data_list = self._fetch_statements(target_date, target_date)
            if not xml_data_list:
                log.write({
                    'state': 'success',
                    'message': 'No statements available for this date.',
                })
                self.last_sync_date = fields.Datetime.now()
                return True

            # Import each statement using the bank parser
            for xml_data in xml_data_list:
                self._import_statement(xml_data)
            log.write({
                'state': 'success',
                'message': f'Imported {len(xml_data_list)} statements.',
            })
            self.last_sync_date = fields.Datetime.now()
            return True
        except Exception as e:  # noqa: BLE001
            _logger.warning('Bank sync failed for %s: %s', self.name, e)
            log.write({
                'state': 'error',
                'message': str(e)[:5000],
            })
            return False

    def _fetch_statements(self, date_from, date_to):
        """Fetch raw XML statements from the bank's API.

        Returns a list of bytes (each entry is one statement XML).
        Subclasses per bank could override this — for now, a generic REST
        implementation with cert auth.
        """
        self.ensure_one()
        endpoint = self._get_endpoint()
        cert_path, key_path, temp_dir = self._get_cert_paths()

        try:
            params = {
                'iban': self.iban,
                'dateFrom': date_from.isoformat(),
                'dateTo': date_to.isoformat(),
            }
            headers = {'Accept': 'application/xml'}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            elif self.api_username and self.api_password:
                import base64 as b64
                creds = b64.b64encode(f'{self.api_username}:{self.api_password}'.encode()).decode()
                headers['Authorization'] = f'Basic {creds}'

            response = requests.get(
                endpoint,
                params=params,
                cert=(cert_path, key_path) if cert_path else None,
                headers=headers,
                timeout=30,
            )
            if response.status_code == 404:
                return []
            response.raise_for_status()
            # Bank may return multiple XML statements concatenated or zipped
            content_type = response.headers.get('Content-Type', '')
            if 'zip' in content_type or response.content[:2] == b'PK':
                return self._extract_zip(response.content)
            if response.content.lstrip().startswith(b'<'):
                return [response.content]
            _logger.warning('Unexpected content type: %s', content_type)
            return []
        finally:
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _extract_zip(self, zip_bytes):
        """Extract XML files from a ZIP archive."""
        import io
        import zipfile
        result = []
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            for name in zf.namelist():
                if name.endswith('.xml'):
                    result.append(zf.read(name))
        return result

    def _import_statement(self, xml_bytes):
        """Use `account_bank_statement_import` to import the statement XML."""
        Import = self.env['account.bank.statement.import'].with_context({
            'journal_id': self.journal_id.id,
        })
        Import.import_file(xml_bytes)
        return True

    @api.model
    def _cron_daily_sync(self):
        """Cron entry: sync all active configs for yesterday."""
        for cfg in self.search([('auto_sync', '=', True), ('active', '=', True)]):
            try:
                cfg._sync_one_day(date.today() - timedelta(days=1))
            except Exception as e:  # noqa: BLE001
                _logger.warning('Daily sync failed for %s: %s', cfg.name, e)
