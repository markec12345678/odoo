# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_si_default_premise_id = fields.Many2one(
        'l10n_si.business.premise', string='Default SI Premise',
        help='Used for outgoing invoices when no premise is set on the move.',
    )
    l10n_si_default_device_id = fields.Many2one(
        'l10n_si.electronic.device', string='Default SI Device',
        help='Used for outgoing invoices when no device is set on the move.',
    )
