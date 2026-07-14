# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    # Croatian invoice numbering & references
    payment_model = fields.Char(
        string="Payment Model",
        size=3,
        default="HR01",
        help="Croatian payment model (HR01 = invoice reference, HR02 = contract).",
    )
    payment_reference = fields.Char(
        string="Poziv na broj (primatelja)",
        help="Reference number for the payee — used in Croatian bank transfers.",
    )
    location_code = fields.Char(
        string="Location Code",
        size=2,
        help="Croatian invoice numbering uses a 2-digit location code "
             "(oznaka poslovnog prostora).",
    )
    cash_register_code = fields.Char(
        string="Cash Register Code",
        size=2,
        help="Croatian invoice numbering uses a 2-digit cash register code "
             "(oznaka naplatnog uređaja).",
    )
