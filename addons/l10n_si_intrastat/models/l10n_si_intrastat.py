# -*- coding: utf-8 -*-
from odoo import api, fields, models

class L10nSiIntrastatReport(models.Model):
    _name = "l10n_si.intrastat.report"
    _description = "Slovenian Intrastat Report"
    _order = "year DESC, month DESC"

    name = fields.Char(compute="_compute_name", store=True)
    number = fields.Char(copy=False, readonly=True, default="/")
    year = fields.Integer(required=True, default=lambda s: fields.Date.today().year)
    month = fields.Integer(required=True, default=lambda s: fields.Date.today().month)
    report_type = fields.Selection([("arrival","Prihodi"),("dispatch","Odhodi")], required=True, default="arrival")
    company_id = fields.Many2one("res.company", string="Company", default=lambda s: s.env.company, required=True)
    state = fields.Selection([("draft","Osnutek"),("computed","Izračunano"),("submitted","Predloženo")], default="draft", tracking=True)
    line_ids = fields.One2many("l10n_si.intrastat.line", "report_id", string="Postavke")
    total_value = fields.Monetary(compute="_compute_totals", store=True, string="Skupna vrednost", currency_field="currency_id")
    currency_id = fields.Many2one("res.currency", related="company_id.currency_id", store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("number","/") == "/":
                vals["number"] = self.env["ir.sequence"].next_by_code("l10n_si.intrastat.report") or "/"
        return super().create(vals_list)

    @api.depends("year","month")
    def _compute_name(self):
        for r in self: r.name = f"Intrastat {r.year}-{r.month:02d}"

    def _compute_totals(self):
        for r in self: r.total_value = sum(r.line_ids.mapped("statistical_value"))

    def action_compute(self):
        for report in self:
            report.line_ids.unlink()
            from datetime import date
            date_from = date(report.year, report.month, 1)
            date_to = date(report.year, 12, 31) if report.month == 12 else date(report.year, report.month + 1, 1)
            moves = self.env["account.move"].search([("date",">=",date_from),("date","<=",date_to),("move_type","=","out_invoice" if report.report_type == "dispatch" else "in_invoice"),("state","=","posted")])
            for move in moves:
                if not move.partner_id.country_id or move.partner_id.country_id.code == "SI" or not move.partner_id.vat:
                    continue
                for line in move.invoice_line_ids:
                    self.env["l10n_si.intrastat.line"].create({
                        "report_id": report.id,
                        "partner_vat": move.partner_id.vat,
                        "partner_country_id": move.partner_id.country_id.id,
                        "commodity_code": line.product_id.default_code or "99999999",
                        "description": line.name,
                        "statistical_value": line.price_subtotal,
                        "net_mass": (line.product_id.weight or 0) * line.quantity,
                        "supplementary_units": line.quantity,
                        "nature_of_transaction": "11",
                        "mode_of_transport": "3",
                    })
            report.state = "computed"

    def action_submit(self):
        self.write({"state": "submitted"})

class L10nSiIntrastatLine(models.Model):
    _name = "l10n_si.intrastat.line"
    _description = "Slovenian Intrastat Line"
    report_id = fields.Many2one("l10n_si.intrastat.report", required=True, ondelete="cascade")
    partner_vat = fields.Char(string="Davčna št. partnerja", required=True)
    partner_country_id = fields.Many2one("res.country", string="Država")
    commodity_code = fields.Char(string="Kombinirana nomenklatura", required=True)
    description = fields.Char(string="Blago")
    statistical_value = fields.Float(string="Statistična vrednost (EUR)")
    net_mass = fields.Float(string="Neto masa (kg)")
    supplementary_units = fields.Float(string="Dopolnilne enote")
    nature_of_transaction = fields.Char(default="11", size=2)
    mode_of_transport = fields.Selection([("1","Letalski"),("2","Železniški"),("3","Cestni"),("4","Morski"),("5","Pošta"),("7","Cevovod"),("8","Notranji"),("9","Neznano")], default="3")

