# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    si_bank_sync_config_id = fields.Many2one(
        'l10n_si.bank.sync.config', string='SI Bank Sync Config',
        help='When set, statements for this journal are auto-fetched daily.',
    )
