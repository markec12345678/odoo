# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class L10nSiFiscalResubmitWizard(models.TransientModel):
    """Wizard for batch resubmission of failed FURS submissions."""
    _name = 'l10n_si.fiscal.resubmit.wizard'
    _description = 'SI Fiscal: Batch Resubmit Wizard'

    move_ids = fields.Many2many('account.move', string='Invoices', required=True)

    def action_resubmit(self):
        for move in self.move_ids:
            move._si_fiscal_submit_to_furs()
        return {'type': 'ir.actions.act_window_close'}
