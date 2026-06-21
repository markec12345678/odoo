# -*- coding: utf-8 -*-
from odoo import fields, models


class L10nSiBankSyncLog(models.Model):
    _name = 'l10n_si.bank.sync.log'
    _description = 'Slovenian Bank Sync Log'
    _order = 'create_date DESC'

    config_id = fields.Many2one('l10n_si.bank.sync.config', required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', required=True)
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    state = fields.Selection(
        selection=[('pending', 'V teku'),
                   ('success', 'Uspeh'),
                   ('error', 'Napaka')],
        default='pending',
    )
    message = fields.Text()
    statement_count = fields.Integer(default=0)
