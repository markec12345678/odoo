# -*- coding: utf-8 -*-
from odoo import api, fields, models

class L10nSiViesReturn(models.Model):
    _name = "l10n_si.vies.return"
    _description = "Slovenian VIES Return"
    _order = "year DESC, month DESC"

    name = fields.Char(compute="_compute_name", store=True)
    number = fields.Char(copy=False, readonly=True, default="/")
    year = fields.Integer(required=True, default=lambda s: s.env.company.currency_id and fields.Date.today().year or 2026)
    month = fields.Integer(required=True, default=lambda s: fields.Date.today().month)
    company_id = fields.Many2one("res.company", string="Company", default=lambda s: s.env.company, required=True)
    state = fields.Selection([("draft","Osnutek"),("computed","Izračunano"),("submitted","Predloženo")], default="draft", tracking=True)
    line_ids = fields.One2many("l10n_si.vies.line", "return_id", string="Postavke")
    total_value = fields.Monetary(compute="_compute_totals", store=True, string="Skupna vrednost", currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", related="company_id.currency_id", store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("number","/") == "/":
                vals["number"] = self.env["ir.sequence"].next_by_code("l10n_si.vies.return") or "/"
        return super().create(vals_list)

    @api.depends("year","month")
    def _compute_name(self):
        for r in self: r.name = f"VIES {r.year}-{r.month:02d}"

    def _compute_totals(self):
        for r in self: r.total_value = sum(r.line_ids.mapped("total_value"))

    def action_compute(self):
        for report in self:
            report.line_ids.unlink()
            from datetime import date
            date_from = date(report.year, report.month, 1)
            date_to = date(report.year, 12, 31) if report.month == 12 else date(report.year, report.month + 1, 1)
            moves = self.env["account.move"].search([("date",">=",date_from),("date","<=",date_to),("move_type","=","out_invoice"),("state","=","posted"),("company_id","=",report.company_id.id)])
            for move in moves:
                if not move.partner_id.country_id or move.partner_id.country_id.code == "SI" or not move.partner_id.vat:
                    continue
                self.env["l10n_si.vies.line"].create({
                    "return_id": report.id,
                    "partner_vat": move.partner_id.vat,
                    "partner_country_id": move.partner_id.country_id.id,
                    "partner_name": move.partner_id.name,
                    "invoice_number": move.name,
                    "invoice_date": move.invoice_date,
                    "total_value": move.amount_untaxed,
                    "tax_rate": 22.0,
                    "tax_value": move.amount_tax,
                })
            report.state = "computed"

    def action_submit(self):
        self.write({"state": "submitted"})

class L10nSiViesLine(models.Model):
    _name = "l10n_si.vies.line"
    _description = "Slovenian VIES Line"
    return_id = fields.Many2one("l10n_si.vies.return", required=True, ondelete="cascade")
    partner_vat = fields.Char(string="Davčna št. kupca", required=True)
    partner_country_id = fields.Many2one("res.country", string="Država")
    partner_name = fields.Char(string="Ime kupca")
    invoice_number = fields.Char(string="Št. računa")
    invoice_date = fields.Date(string="Datum računa")
    total_value = fields.Float(string="Osnova (EUR)")
    tax_rate = fields.Float(string="Stopnja DDV (%)")
    tax_value = fields.Float(string="DDV (EUR)")

