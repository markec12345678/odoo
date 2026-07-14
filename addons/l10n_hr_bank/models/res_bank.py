# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResBank(models.Model):
    _inherit = "res.bank"

    code = fields.Char(
        string="Bank Code",
        help="Croatian bank code (7 digits, embedded in IBAN digits 5-11). "
             "Used to auto-detect bank from IBAN.",
    )
