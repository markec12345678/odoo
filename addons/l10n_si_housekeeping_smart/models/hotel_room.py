# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HotelRoom(models.Model):
    _inherit = "l10n_si.hotel.room"

    housekeeping_task_ids = fields.One2many(
        "l10n_si.housekeeping.task",
        "room_id",
        string="Housekeeping Tasks",
    )
    open_task_count = fields.Integer(
        compute="_compute_open_task_count",
        string="Open Tasks",
    )
    last_cleaned = fields.Datetime(
        compute="_compute_last_cleaned",
        store=True,
    )

    def _compute_open_task_count(self):
        for room in self:
            room.open_task_count = len(
                room.housekeeping_task_ids.filtered(
                    lambda t: t.state in ("pending", "assigned", "in_progress")
                )
            )

    @api.depends("housekeeping_task_ids.completed_on")
    def _compute_last_cleaned(self):
        for room in self:
            done = room.housekeeping_task_ids.filtered(
                lambda t: t.state == "done" and t.completed_on
            )
            if done:
                room.last_cleaned = max(done.mapped("completed_on"))
            else:
                room.last_cleaned = False

    def action_view_housekeeping_tasks(self):
        """Open housekeeping tasks for this room."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Housekeeping Tasks",
            "res_model": "l10n_si.housekeeping.task",
            "view_mode": "kanban,tree,form",
            "domain": [("room_id", "=", self.id)],
            "context": {"default_room_id": self.id},
        }
