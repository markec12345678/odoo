# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    @api.onchange("acc_number")
    def _onchange_acc_number_detect_hr_bank(self):
        """Auto-detect the Croatian bank from the IBAN's bank code.

        Croatian IBAN format: HR + 2 check digits + 7-digit bank code + 10 account digits.
        The 7-digit bank code uniquely identifies the bank.
        """
        for bank in self:
            iban = (bank.acc_number or "").replace(" ", "").upper()
            if not iban.startswith("HR") or len(iban) < 11:
                return
            bank_code = iban[4:11]
            # Look up res.bank by code (we store HR bank code in `code` field)
            hr_bank = self.env["res.bank"].search(
                [("code", "=", bank_code)], limit=1
            )
            if hr_bank:
                bank.bank_id = hr_bank.id
