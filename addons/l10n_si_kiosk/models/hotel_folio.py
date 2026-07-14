# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class HotelFolio(models.Model):
    _inherit = "l10n_si.hotel.folio"

    def action_view_kiosk_sessions(self):
        """Open kiosk sessions related to this folio."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Kiosk Sessions",
            "res_model": "l10n_si.kiosk.session",
            "view_mode": "tree,form",
            "domain": [("folio_id", "=", self.id)],
            "context": {"default_folio_id": self.id},
        }
