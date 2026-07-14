# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class GenerateMonthlyReportWizard(models.TransientModel):
    """Wizard to manually generate a monthly report for a specific
    establishment, year, and month.
    """
    _name = "l10n_si.monthly.ajpes.generate.wizard"
    _description = "Generate Monthly AJPES Report"

    establishment_id = fields.Many2one(
        "l10n_si.etourism.establishment",
        required=True,
    )
    year = fields.Integer(required=True, default=fields.Date.today().year)
    month = fields.Selection(
        [
            (1, "January"), (2, "February"), (3, "March"),
            (4, "April"), (5, "May"), (6, "June"),
            (7, "July"), (8, "August"), (9, "September"),
            (10, "October"), (11, "November"), (12, "December"),
        ],
        required=True,
        default=fields.Date.today().month,
    )
    auto_submit = fields.Boolean(
        default=False,
        help="Automatically submit to AJPES after generation.",
    )

    def action_generate(self):
        """Create and generate the report."""
        self.ensure_one()
        # Check if already exists
        existing = self.env["l10n_si.monthly.ajpes.report"].search(
            [
                ("establishment_id", "=", self.establishment_id.id),
                ("year", "=", self.year),
                ("month", "=", self.month),
            ],
            order="version desc",
            limit=1,
        )
        if existing:
            # Create a new version
            report = self.env["l10n_si.monthly.ajpes.report"].create(
                {
                    "establishment_id": self.establishment_id.id,
                    "year": self.year,
                    "month": self.month,
                    "version": existing.version + 1,
                }
            )
        else:
            report = self.env["l10n_si.monthly.ajpes.report"].create(
                {
                    "establishment_id": self.establishment_id.id,
                    "year": self.year,
                    "month": self.month,
                    "version": 1,
                }
            )
        report.action_generate()
        if self.auto_submit:
            report.action_submit_to_ajpes()
        return {
            "type": "ir.actions.act_window",
            "name": "Monthly Report",
            "res_model": "l10n_si.monthly.ajpes.report",
            "res_id": report.id,
            "view_mode": "form",
            "target": "current",
        }
