# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class GenerateTasksWizard(models.TransientModel):
    """Wizard to manually generate turnover tasks for check-outs on a date."""
    _name = "l10n_si.housekeeping.generate.tasks.wizard"
    _description = "Generate Housekeeping Tasks"

    date = fields.Date(
        required=True,
        default=fields.Date.today,
        help="Generate turnover tasks for all folios checking out on this date.",
    )
    auto_assign = fields.Boolean(
        default=True,
        help="Automatically assign tasks to teams based on floor zones.",
    )
    created_count = fields.Integer(readonly=True)

    def action_generate(self):
        """Generate turnover tasks for all check-outs on the selected date."""
        self.ensure_one()
        task_model = self.env["l10n_si.housekeeping.task"]
        # Find all folios with check-out on this date that don't have a task yet
        folios = self.env["l10n_si.hotel.folio"].search(
            [
                ("check_out", ">=", fields.Datetime.to_string(self.date) + " 00:00:00"),
                ("check_out", "<=", fields.Datetime.to_string(self.date) + " 23:59:59"),
                ("state", "in", ["open", "closed"]),
            ]
        )
        created = 0
        for folio in folios:
            task_id = task_model._auto_create_turnover_task(folio)
            if task_id:
                created += 1
        # Auto-balance if requested
        if self.auto_assign and created:
            task_model._balance_workload(self.date)
        self.created_count = created
        return {
            "type": "ir.actions.act_window",
            "name": "Generated Tasks",
            "res_model": "l10n_si.housekeeping.task",
            "view_mode": "kanban,tree,form",
            "domain": [
                ("scheduled_date", ">=", fields.Datetime.to_string(self.date) + " 00:00:00"),
                ("scheduled_date", "<=", fields.Datetime.to_string(self.date) + " 23:59:59"),
            ],
            "target": "current",
        }
