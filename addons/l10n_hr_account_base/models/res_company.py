# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # Croatian company-specific fields
    court_registration_number = fields.Char(
        string="Court Reg. Number (MBS)",
        help="Matični broj subjekta — court registration number.",
    )
    court_name = fields.Char(
        string="Court of Registration",
        help="Name of the commercial court where the company is registered.",
    )
    share_capital = fields.Float(
        string="Share Capital (HRK/EUR)",
        help="Temeljni kapital — registered share capital.",
    )
    # IBAN and bank info come from res.partner.bank
    # Tax and VAT come from standard Odoo company fields (vat, etc.)
    # Activity classification (NKD) comes from l10n_hr_nkd module
