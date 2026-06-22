# -*- coding: utf-8 -*-
from odoo import api, fields, models

class L10nSiYearEndClose(models.Model):
    _name = "l10n_si.year.end.close"
    _description = "Slovenian Year-End Close"
    _order = "year DESC"

    name = fields.Char(compute="_compute_name", store=True)
    number = fields.Char(copy=False, readonly=True, default="/")
    year = fields.Integer(required=True, default=lambda s: fields.Date.today().year)
    company_id = fields.Many2one("res.company", string="Company", default=lambda s: s.env.company, required=True)
    state = fields.Selection([("draft","Osnutek"),("computed","Izračunano"),("posted","Knjiženo"),("closed","Zaključeno")], default="draft", tracking=True)
    profit_loss_account_id = fields.Many2one("account.account", string="Konto izida (990)")
    closing_account_id = fields.Many2one("account.account", string="Konto zaključne knjižbe (999)")
    net_profit = fields.Monetary(string="Čisti dobiček/izguba", currency_field="currency_id", readonly=True)
    move_id = fields.Many2one("account.move", string="Zaključni list", readonly=True, copy=False)
    currency_id = fields.Many2one("res.currency", related="company_id.currency_id", store=True)
    computed_on = fields.Datetime(readonly=True, copy=False)
    posted_on = fields.Datetime(readonly=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("number","/") == "/":
                vals["number"] = self.env["ir.sequence"].next_by_code("l10n_si.year.end.close") or "/"
        return super().create(vals_list)

    @api.depends("year")
    def _compute_name(self):
        for r in self: r.name = f"Zaključitev {r.year}"

    def action_compute(self):
        for close in self:
            from datetime import date
            lines = self.env["account.move.line"].search([
                ("date",">=",date(close.year,1,1)),("date","<=",date(close.year,12,31)),
                ("parent_state","=","posted"),("company_id","=",close.company_id.id),
            ])
            revenue = sum(lines.filtered(lambda l: l.account_id.account_type == "income").mapped("balance"))
            expense = sum(lines.filtered(lambda l: l.account_id.account_type == "expense").mapped("balance"))
            close.net_profit = revenue + expense
            close.state = "computed"
            close.computed_on = fields.Datetime.now()

    def action_post(self):
        for close in self:
            if not close.profit_loss_account_id: continue
            move = self.env["account.move"].create({"ref": f"Zaključni list {close.year}","move_type":"entry","date":fields.Date.today(),"company_id":close.company_id.id})
            close.move_id = move.id
            close.state = "posted"
            close.posted_on = fields.Datetime.now()

    def action_close(self):
        self.write({"state": "closed"})
