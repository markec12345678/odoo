# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class FiskalDiscountReason(models.Model):
    """UNTDID 5189 — Discount reason code for Fiskalizacija 2.0.

    Used in eRačun B2B XML to indicate why a discount was applied.
    """
    _name = "l10n_hr.fiskal.discount.reason"
    _description = "Fiskal 2.0 Discount Reason (UNTDID 5189)"
    _order = "code"
    _rec_name = "code"

    code = fields.Char(required=True, size=3)
    name = fields.Char(required=True, translate=True)
    name_hr = fields.Char(string="Name (HR)")
    description = fields.Text(translate=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
    )

    _sql_constraints = [
        ("code_unique", "UNIQUE(code)", "Discount reason code must be unique."),
    ]
