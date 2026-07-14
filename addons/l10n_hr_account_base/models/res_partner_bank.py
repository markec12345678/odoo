# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    # Croatian payment system fields
    payment_model = fields.Char(
        string="Payment Model",
        size=3,
        help="Croatian payment model (e.g. HR01 for invoice reference). "
             "Used in HUB3 QR codes and bank transfer forms.",
    )
    payment_reference = fields.Char(
        string="Payment Reference (Poziv na broj)",
        help="Reference number for the payee — used in Croatian bank transfers.",
    )
    bank_code = fields.Char(
        string="Bank Code",
        size=7,
        help="Croatian bank code (first 7 digits of IBAN).",
    )

    def _get_bank_code(self):
        """Extract bank code from IBAN (digits 5-11)."""
        self.ensure_one()
        iban = self.sanitized_acc_number or ""
        # HR IBAN: HR + 2 check digits + 7 bank code + rest
        if iban.startswith("HR") and len(iban) >= 11:
            return iban[4:11]
        return ""
