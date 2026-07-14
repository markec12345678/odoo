# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    # Croatian journal-specific fields
    location_code = fields.Char(
        string="Location Code",
        size=2,
        help="Oznaka poslovnog prostora (2-digit location code for fiscal).",
    )
    cash_register_code = fields.Char(
        string="Cash Register Code",
        size=2,
        help="Oznaka naplatnog uređaja (2-digit cash register code for fiscal).",
    )
