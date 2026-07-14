# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class HotelFolio(models.Model):
    _inherit = "l10n_si.hotel.folio"

    def action_check_out(self):
        """Override to auto-create a turnover housekeeping task on checkout."""
        # Find the parent action_check_out if it exists
        result = True
        # Try calling the parent method (etourism extension)
        if hasattr(super(), "action_check_out"):
            result = super().action_check_out()
        # Auto-create turnover task
        task_model = self.env["l10n_si.housekeeping.task"]
        for folio in self:
            task_model._auto_create_turnover_task(folio)
        return result

    def action_view_housekeeping_tasks(self):
        """Open housekeeping tasks linked to this folio."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Housekeeping Tasks",
            "res_model": "l10n_si.housekeeping.task",
            "view_mode": "kanban,tree,form",
            "domain": [("folio_id", "=", self.id)],
        }
