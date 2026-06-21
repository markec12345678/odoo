# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class L10nSiElectronicDevice(models.Model):
    """Slovenian 'elektronska naprava' (cash register / device).

    Each device has a code (e.g. 'KASA1', 'BLAG1') and is registered with FURS
    within the parent poslovni prostor.
    """
    _name = 'l10n_si.electronic.device'
    _description = 'Slovenian Electronic Device (Cash Register)'
    _order = 'business_premise_id, code'

    name = fields.Char(string='Device Name', required=True, translate=True)
    code = fields.Char(
        string='Device Code',
        required=True,
        help='Short code identifying this device in invoice numbers. '
             'Max 20 chars, alphanumeric.',
        size=20,
    )
    business_premise_id = fields.Many2one(
        'l10n_si.business.premise', string='Business Premise',
        required=True, ondelete='restrict',
    )
    company_id = fields.Many2one(
        'res.company', related='business_premise_id.company_id',
        string='Company', store=True,
    )
    active = fields.Boolean(default=True)
    furs_device_id = fields.Char(string='FURS Device ID', readonly=True, copy=False)
    furs_registered_on = fields.Datetime(string='FURS Registered On', readonly=True, copy=False)
    sequence_ids = fields.One2many(
        'ir.sequence', 'l10n_si_device_id', string='Yearly Sequences',
    )

    _sql_constraints = [
        ('code_premise_uniq', 'unique(code, business_premise_id)',
         'Device code must be unique within a business premise.'),
    ]

    @api.constrains('code')
    def _check_code_format(self):
        for device in self:
            if not device.code or not device.code.isalnum():
                raise ValidationError(_(
                    'Device code must be alphanumeric. Got: %s',
                ) % device.code)

    def _get_or_create_yearly_sequence(self, year=None):
        """Return the ir.sequence for this device in the given year (creates it if missing).

        Format: <premise>-<device>-<year>-<5-digit serial>
        Example: BL1-KASA1-2025-00001
        """
        self.ensure_one()
        year = year or fields.Date.today().year
        Sequence = self.env['ir.sequence']
        seq = Sequence.search([
            ('l10n_si_device_id', '=', self.id),
            ('l10n_si_year', '=', str(year)),
        ], limit=1)
        if seq:
            return seq

        premise = self.business_premise_id
        prefix = f"{premise.code}-{self.code}-{year}-"
        seq = Sequence.create({
            'name': f'SI {premise.code}/{self.code} {year}',
            'code': f'l10n_si.{premise.code}.{self.code}.{year}',
            'prefix': prefix,
            'padding': 5,
            'number_next': 1,
            'number_increment': 1,
            'implementation': 'standard',
            'use_date_range': False,
            'l10n_si_device_id': self.id,
            'l10n_si_year': str(year),
            'company_id': self.company_id.id,
        })
        return seq

    @api.model
    def _cron_refresh_yearly_sequences(self):
        """Cron entry: pre-create ir.sequence rows for all active devices for the current year.

        This avoids a race condition where two invoices are issued at 00:00 on Jan 1st
        before the new sequence has been created.
        """
        year = fields.Date.today().year
        for device in self.search([('active', '=', True)]):
            try:
                device._get_or_create_yearly_sequence(year=year)
            except Exception as e:  # noqa: BLE001
                _logger = self.env['ir.logging']
                _logger.sudo().create({
                    'name': 'l10n_si_sequence.cron',
                    'type': 'server',
                    'level': 'ERROR',
                    'message': f'Failed to refresh sequence for device {device.code}: {e}',
                    'path': 'l10n_si_sequence/models/l10n_si_electronic_device.py',
                    'line': '0',
                    'func': '_cron_refresh_yearly_sequences',
                })
