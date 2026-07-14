# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class FiskalDocumentType(models.Model):
    """UNTDID 1001 — Document type code for Fiskalizacija 2.0.

    Specifies the type of document being submitted (invoice, credit note, etc.).
    """
    _name = "l10n_hr.fiskal.document.type"
    _description = "Fiskal 2.0 Document Type (UNTDID 1001)"
    _order = "code"
    _rec_name = "code"

    code = fields.Char(required=True, size=3, help="UNTDID 1001 code (e.g. 380).")
    name = fields.Char(required=True, translate=True)
    name_hr = fields.Char(string="Name (HR)")
    description = fields.Text(translate=True)
    active = fields.Boolean(default=True)
    is_invoice = fields.Boolean(
        default=False,
        help="True if this code represents an invoice (380, 384, 389).",
    )
    is_credit_note = fields.Boolean(
        default=False,
        help="True if this is a credit note (381).",
    )
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
    )

    _sql_constraints = [
        ("code_unique", "UNIQUE(code)", "Document type code must be unique."),
    ]
