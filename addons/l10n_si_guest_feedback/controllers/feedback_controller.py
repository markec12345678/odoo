# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import _, fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)


class FeedbackController(http.Controller):
    """Public feedback controller — token-authenticated, no login."""

    def _get_response(self, token):
        if not token:
            return request.env["l10n_si.feedback.response"]
        return request.env["l10n_si.feedback.response"].sudo().search(
            [("token", "=", token)], limit=1
        )

    @http.route("/feedback/start/<string:token>", type="http", auth="public", website=True)
    def feedback_start(self, token, **kw):
        """Show the feedback form."""
        response = self._get_response(token)
        if not response:
            return request.not_found(_("Invalid or expired feedback link."))
        if response.state == "expired":
            return request.render("l10n_si_guest_feedback.expired", {})
        if response.state == "completed":
            return request.render(
                "l10n_si_guest_feedback.already_completed",
                {"response": response},
            )
        response.action_mark_started()
        return request.render(
            "l10n_si_guest_feedback.form",
            {
                "response": response,
                "survey": response.survey_id,
            },
        )

    @http.route("/feedback/submit/<string:token>", type="http", auth="public", website=True, methods=["POST"])
    def feedback_submit(self, token, **kw):
        """Submit the feedback."""
        response = self._get_response(token)
        if not response:
            return request.not_found(_("Invalid feedback link."))
        response.action_complete(kw)
        return request.render(
            "l10n_si_guest_feedback.thank_you",
            {
                "response": response,
                "survey": response.survey_id,
            },
        )

    @http.route("/feedback/preview/<int:survey_id>", type="http", auth="user", website=True)
    def feedback_preview(self, survey_id, **kw):
        """Admin preview of a survey."""
        survey = request.env["l10n_si.feedback.survey"].browse(survey_id)
        if not survey.exists():
            return request.not_found(_("Survey not found."))
        return request.render(
            "l10n_si_guest_feedback.preview",
            {
                "survey": survey,
                "is_preview": True,
            },
        )

    @http.route("/feedback/dashboard/data", type="json", auth="user", website=True)
    def feedback_dashboard_data(self, **kw):
        """JSON endpoint for real-time dashboard refresh."""
        Response = request.env["l10n_si.feedback.response"]
        today_start = fields.Datetime.to_string(fields.Date.today()) + " 00:00:00"
        today_responses = Response.search_count(
            [("completed_date", ">=", today_start)]
        )
        today_alerts = request.env["l10n_si.feedback.alert"].search_count(
            [("create_date", ">=", today_start), ("state", "=", "open")]
        )
        week_ago = fields.Datetime.to_string(
            fields.Date.today().replace(day=max(1, fields.Date.today().day - 7))
        ) + " 00:00:00"
        week_responses = Response.search_count(
            [("completed_date", ">=", week_ago)]
        )
        # Avg score this week
        week_scored = Response.search(
            [("completed_date", ">=", week_ago), ("overall_score", ">", 0)]
        )
        avg_week = 0.0
        if week_scored:
            avg_week = sum(r.overall_score for r in week_scored) / len(week_scored)
        return {
            "today_responses": today_responses,
            "today_alerts": today_alerts,
            "week_responses": week_responses,
            "avg_week_score": round(avg_week, 2),
        }
