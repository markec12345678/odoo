# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class EtourismEstablishment(models.Model):
    _inherit = "l10n_si.etourism.establishment"

    monthly_report_ids = fields.One2many(
        "l10n_si.monthly.ajpes.report",
        "establishment_id",
        string="Monthly Reports",
    )
    monthly_report_count = fields.Integer(compute="_compute_monthly_report_count")
    last_report_date = fields.Datetime(compute="_compute_monthly_report_count")

    def _compute_monthly_report_count(self):
        for est in self:
            reports = est.monthly_report_ids
            est.monthly_report_count = len(reports)
            if reports:
                est.last_report_date = max(
                    r.generated_on or r.create_date for r in reports
                )
            else:
                est.last_report_date = False

    def action_view_monthly_reports(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Monthly AJPES Reports",
            "res_model": "l10n_si.monthly.ajpes.report",
            "view_mode": "tree,form",
            "domain": [("establishment_id", "=", self.id)],
            "context": {"default_establishment_id": self.id},
        }
