# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HousekeepingTeam(models.Model):
    """A team of housekeepers assigned to a specific shift/zone.

    Allows for zone-based scheduling (e.g. Team A = floors 1-3,
    Team B = floors 4-6) and shift rotation.
    """
    _name = "l10n_si.housekeeping.team"
    _description = "Housekeeping Team"
    _inherit = ["mail.thread"]
    _order = "name"

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,
    )
    leader_id = fields.Many2one(
        "hr.employee",
        string="Team Leader",
        tracking=True,
    )
    member_ids = fields.Many2many(
        "hr.employee",
        "housekeeping_team_member_rel",
        "team_id",
        "employee_id",
        string="Members",
    )
    member_count = fields.Integer(compute="_compute_member_count")

    # --- Zone assignment --------------------------------------------------
    floor_from = fields.Integer(help="Lowest floor this team handles.")
    floor_to = fields.Integer(help="Highest floor this team handles.")
    zone = fields.Char(
        help="Free-form zone label, e.g. 'Wing A', 'Pool villas'.",
    )

    # --- Shift ------------------------------------------------------------
    shift_start = fields.Float(string="Shift start (h)", default=8.0)
    shift_end = fields.Float(string="Shift end (h)", default=16.0)
    color = fields.Integer(default=0)

    # --- Stats ------------------------------------------------------------
    task_ids = fields.One2many(
        "l10n_si.housekeeping.task",
        "team_id",
        string="Tasks",
    )
    open_task_count = fields.Integer(compute="_compute_task_stats")
    done_today_count = fields.Integer(compute="_compute_task_stats")
    avg_duration_minutes = fields.Float(compute="_compute_task_stats")

    def _compute_member_count(self):
        for t in self:
            t.member_count = len(t.member_ids)

    def _compute_task_stats(self):
        today_start = fields.Datetime.to_string(fields.Date.today()) + " 00:00:00"
        today_end = fields.Datetime.to_string(fields.Date.today()) + " 23:59:59"
        for t in self:
            tasks_today = t.task_ids.filtered(
                lambda x: x.scheduled_date >= today_start
                and x.scheduled_date <= today_end
            )
            t.open_task_count = len(
                tasks_today.filtered(lambda x: x.state in ("pending", "assigned", "in_progress"))
            )
            t.done_today_count = len(
                tasks_today.filtered(lambda x: x.state == "done")
            )
            done_with_duration = tasks_today.filtered(
                lambda x: x.state == "done" and x.duration_minutes > 0
            )
            if done_with_duration:
                t.avg_duration_minutes = sum(
                    done_with_duration.mapped("duration_minutes")
                ) / len(done_with_duration)
            else:
                t.avg_duration_minutes = 0.0

    def action_view_tasks(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Tasks",
            "res_model": "l10n_si.housekeeping.task",
            "view_mode": "kanban,tree,form",
            "domain": [("team_id", "=", self.id)],
            "context": {"default_team_id": self.id},
        }
