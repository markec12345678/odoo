# -*- coding: utf-8 -*-
from odoo import api, fields, models

class L10nSiAuditTrail(models.Model):
    _name = "l10n_si.audit.trail"
    _description = "Slovenian Audit Trail"
    _order = "create_date DESC"

    name = fields.Char(compute="_compute_name", store=True)
    user_id = fields.Many2one("res.users", string="Uporabnik", required=True, default=lambda s: s.env.user, readonly=True)
    model_name = fields.Char(string="Model", required=True, readonly=True)
    record_id = fields.Integer(string="ID zapisa", required=True, readonly=True)
    record_name = fields.Char(string="Ime zapisa", readonly=True)
    action_type = fields.Selection([("create","Ustvarjeno"),("write","Spremenjeno"),("unlink","Izbrisano")], required=True, readonly=True)
    field_name = fields.Char(string="Polje", readonly=True)
    old_value = fields.Text(string="Stara vrednost", readonly=True)
    new_value = fields.Text(string="Nova vrednost", readonly=True)
    ip_address = fields.Char(readonly=True)
    company_id = fields.Many2one("res.company", string="Company", default=lambda s: s.env.company, required=True)

    @api.depends("model_name","record_name","action_type")
    def _compute_name(self):
        for r in self: r.name = f"{r.action_type} - {r.model_name} ({r.record_name or r.record_id})"

class Base(models.AbstractModel):
    _inherit = "base"
    sensitive_fields = ["price_unit", "list_price", "standard_price", "vat", "amount_total", "tax_ids", "l10n_si_zoi", "l10n_si_eor"]
    def write(self, vals):
        tracked = [f for f in self.sensitive_fields if f in vals]
        if tracked and self.env.user and not self.env.context.get("no_audit"):
            for record in self:
                for field in tracked:
                    old = getattr(record, field, None)
                    new = vals[field]
                    if old != new:
                        self.env["l10n_si.audit.trail"].sudo().create({
                            "model_name": self._name, "record_id": record.id,
                            "record_name": record.display_name, "action_type": "write",
                            "field_name": field, "old_value": str(old), "new_value": str(new),
                        })
        return super().write(vals)
