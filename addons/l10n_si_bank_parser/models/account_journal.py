# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    si_bank_format = fields.Selection(
        selection=[('camt053', 'ISO 20022 CAMT.053 (XML)'),
                   ('mt940', 'MT940 (STA, legacy)')],
        string='SI Bank Statement Format',
        help='Format used when importing statements for this journal.',
    )
    si_bank_identifier = fields.Char(
        string='SI Bank Identifier (BIC)',
        help='Bank BIC code (e.g. LJBASI2X for NLB). Used for auto-detection '
             'when multiple journals have the same currency.',
    )
