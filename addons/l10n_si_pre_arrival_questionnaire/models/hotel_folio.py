# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HotelFolio(models.Model):
    _inherit = "l10n_si.hotel.folio"

    questionnaire_response_id = fields.Many2one(
        "l10n_si.questionnaire.response",
        string="Pre-arrival Questionnaire",
        ondelete="set null",
    )
    questionnaire_state = fields.Selection(
        related="questionnaire_response_id.state",
        store=True,
        string="Questionnaire State",
    )
    questionnaire_completed = fields.Boolean(
        compute="_compute_questionnaire_completed",
        store=True,
    )
    has_dietary_alert = fields.Boolean(
        compute="_compute_questionnaire_completed",
        store=True,
        help="True if guest has dietary restrictions or allergies.",
    )
    dietary_summary = fields.Char(
        compute="_compute_questionnaire_completed",
        store=True,
        help="Short text summarizing dietary needs for the kitchen.",
    )

    @api.depends(
        "questionnaire_response_id.state",
        "questionnaire_response_id.dietary_restrictions",
        "questionnaire_response_id.allergies",
    )
    def _compute_questionnaire_completed(self):
        for folio in self:
            resp = folio.questionnaire_response_id
            folio.questionnaire_completed = bool(resp and resp.state == "completed")
            dietary = []
            if resp:
                if resp.dietary_restrictions:
                    dietary.append(resp.dietary_restrictions)
                if resp.allergies:
                    dietary.append(f"ALLERGIES: {resp.allergies}")
            folio.dietary_summary = " | ".join(dietary)
            folio.has_dietary_alert = bool(dietary)

    def action_view_questionnaire(self):
        """Open the questionnaire response for this folio."""
        self.ensure_one()
        if self.questionnaire_response_id:
            return {
                "type": "ir.actions.act_window",
                "name": "Pre-arrival Questionnaire",
                "res_model": "l10n_si.questionnaire.response",
                "res_id": self.questionnaire_response_id.id,
                "view_mode": "form",
            }
        return {
            "type": "ir.actions.act_window",
            "name": "Pre-arrival Questionnaire",
            "res_model": "l10n_si.questionnaire.response",
            "view_mode": "form",
            "context": {
                "default_folio_id": self.id,
                "default_partner_id": self.partner_id.id,
            },
        }

    def action_send_questionnaire(self):
        """Create a questionnaire response (with token) and send it via email."""
        for folio in self:
            if not folio.partner_id or not folio.partner_id.email:
                continue
            if folio.questionnaire_response_id:
                continue
            # Find the active template for this company
            template = folio.env["l10n_si.questionnaire.template"].search(
                [
                    ("active", "=", True),
                    ("company_id", "in", [folio.company_id.id, False]),
                ],
                order="sequence asc",
                limit=1,
            )
            if not template:
                continue
            from datetime import timedelta

            expire = False
            if folio.check_in:
                expire = folio.check_in + timedelta(days=1)
            response = folio.env["l10n_si.questionnaire.response"].create(
                {
                    "template_id": template.id,
                    "folio_id": folio.id,
                    "partner_id": folio.partner_id.id,
                    "state": "sent",
                    "sent_date": fields.Datetime.now(),
                    "expire_date": expire,
                }
            )
            folio.questionnaire_response_id = response.id
            # Send email with the link
            response._send_link_email()
        return True
