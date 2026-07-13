# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class IrSequence(models.Model):
    """Extend ir.sequence to track the SI device and year it belongs to."""
    _inherit = 'ir.sequence'

    l10n_si_device_id = fields.Many2one(
        'l10n_si.electronic.device', string='SI Device',
        ondelete='cascade', index=True,
    )
    l10n_si_year = fields.Char(string='SI Year', size=4, index=True)
