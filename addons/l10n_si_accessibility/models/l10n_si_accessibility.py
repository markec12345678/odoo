# -*- coding: utf-8 -*-
from odoo import api, fields, models

class L10n_si_accessibility_feature (models.Model):
    _name = "l10n_si.accessibility.feature"
    _description = "Slovenian Accessibility"
    _order = "create_date DESC"

    name = fields.Char(required=True, string="Naziv")
    number = fields.Char(copy=False, readonly=True, default="/")
    active = fields.Boolean(default=True)
    company_id = fields.Many2one("res.company", string="Company", default=lambda s: s.env.company, required=True)
    notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("number","/") == "/":
                vals["number"] = self.env["ir.sequence"].next_by_code("l10n_si.accessibility.feature") or "/"
        return super().create(vals_list)
