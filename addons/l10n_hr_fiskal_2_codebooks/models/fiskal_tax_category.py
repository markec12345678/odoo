# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class FiskalTaxCategory(models.Model):
    """UNTDID 5305/5153 — Tax category code for Fiskalizacija 2.0.

    Specifies the VAT category for each invoice line in eRačun B2B XML.
    """
    _name = "l10n_hr.fiskal.tax.category"
    _description = "Fiskal 2.0 Tax Category (UNTDID 5305/5153)"
    _order = "code"
    _rec_name = "code"

    code = fields.Char(
        required=True,
        size=3,
        help="UNTDID 5305 code (e.g. S, Z, E, AE, K, G, O).",
    )
    name = fields.Char(required=True, translate=True)
    name_hr = fields.Char(string="Name (HR)")
    description = fields.Text(translate=True)
    active = fields.Boolean(default=True)
    is_exempt = fields.Boolean(
        default=False,
        help="True if this category is tax-exempt (E, AE, K, G, O).",
    )
    requires_exemption_reason = fields.Boolean(
        default=False,
        help="True if a VATEX exemption reason must be specified.",
    )
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
    )

    _sql_constraints = [
        ("code_unique", "UNIQUE(code)", "Tax category code must be unique."),
    ]
