# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HotelFolio(models.Model):
    _inherit = "l10n_si.hotel.folio"

    feedback_response_ids = fields.One2many(
        "l10n_si.feedback.response",
        "folio_id",
        string="Feedback Responses",
    )
    feedback_response_count = fields.Integer(
        compute="_compute_feedback_response_count"
    )
    feedback_avg_score = fields.Float(
        compute="_compute_feedback_response_count",
        help="Average overall score from all feedback responses.",
    )
    has_feedback_alert = fields.Boolean(
        compute="_compute_feedback_response_count",
        help="True if any feedback response has a low-score alert.",
    )

    def _compute_feedback_response_count(self):
        for folio in self:
            responses = folio.feedback_response_ids.filtered(
                lambda r: r.state == "completed"
            )
            folio.feedback_response_count = len(responses)
            scored = responses.filtered(lambda r: r.overall_score > 0)
            if scored:
                folio.feedback_avg_score = round(
                    sum(r.overall_score for r in scored) / len(scored), 2
                )
            else:
                folio.feedback_avg_score = 0.0
            folio.has_feedback_alert = any(r.has_alert for r in responses)

    def action_view_feedback(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Guest Feedback",
            "res_model": "l10n_si.feedback.response",
            "view_mode": "tree,form",
            "domain": [("folio_id", "=", self.id)],
            "context": {"default_folio_id": self.id},
        }

    def action_send_feedback_request(self):
        """Create a feedback response (with token) for this folio and
        send the link to the guest.
        """
        for folio in self:
            if not folio.partner_id or not folio.partner_id.email:
                continue
            # Find an active mid-stay survey
            survey = folio.env["l10n_si.feedback.survey"].search(
                [
                    ("active", "=", True),
                    ("company_id", "in", [folio.company_id.id, False]),
                    ("trigger", "=", "mid_stay"),
                ],
                order="sequence asc",
                limit=1,
            )
            if not survey:
                continue
            existing = folio.env["l10n_si.feedback.response"].search(
                [
                    ("folio_id", "=", folio.id),
                    ("survey_id", "=", survey.id),
                    ("state", "in", ["sent", "started"]),
                ],
                limit=1,
            )
            if existing:
                continue
            response = folio.env["l10n_si.feedback.response"].create(
                {
                    "survey_id": survey.id,
                    "folio_id": folio.id,
                    "partner_id": folio.partner_id.id,
                    "state": "sent",
                    "sent_date": fields.Datetime.now(),
                }
            )
            response._send_link_email()
        return True
