# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    fiskal_tax_category_id = fields.Many2one(
        "l10n_hr.fiskal.tax.category",
        string="Fiskal Tax Category",
        help="UNTDID 5305 category for Fiskalizacija 2.0 eRačun B2B.",
    )
