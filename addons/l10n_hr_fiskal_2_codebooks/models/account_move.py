# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    fiskal_document_type_id = fields.Many2one(
        "l10n_hr.fiskal.document.type",
        string="Fiskal Document Type",
        help="UNTDID 1001 document type for Fiskalizacija 2.0.",
        compute="_compute_fiskal_document_type",
        store=True,
        readonly=False,
    )
    fiskal_discount_reason_id = fields.Many2one(
        "l10n_hr.fiskal.discount.reason",
        string="Fiskal Discount Reason",
        help="UNTDID 5189 reason for any discounts on this invoice.",
    )

    def _compute_fiskal_document_type(self):
        """Auto-detect based on move_type."""
        type_map = {
            "out_invoice": "380",  # Commercial invoice
            "out_refund": "381",  # Credit note
            "out_receipt": "384",  # Corrected invoice
        }
        for move in self:
            if move.fiskal_document_type_id:
                continue
            code = type_map.get(move.move_type)
            if code:
                doc_type = self.env["l10n_hr.fiskal.document.type"].search(
                    [("code", "=", code)], limit=1
                )
                if doc_type:
                    move.fiskal_document_type_id = doc_type.id
