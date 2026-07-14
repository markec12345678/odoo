# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class FeedbackSurvey(models.Model):
    """A reusable feedback survey definition — what to ask guests.

    A survey groups questions and is sent at a specific point in the journey
    (arrival day, mid-stay, post-stay).
    """
    _name = "l10n_si.feedback.survey"
    _description = "Guest Feedback Survey"
    _inherit = ["mail.thread"]
    _order = "sequence, id"

    name = fields.Char(required=True, tracking=True, translate=True)
    active = fields.Boolean(default=True, tracking=True)
    sequence = fields.Integer(default=10)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,
    )
    description = fields.Html(sanitize=True)

    # --- Trigger ----------------------------------------------------------
    trigger = fields.Selection(
        [
            ("arrival_day", "Arrival day (evening)"),
            ("mid_stay", "Mid-stay"),
            ("check_out_day", "Check-out day"),
            ("post_stay", "Post-stay (24h after)"),
            ("manual", "Manual (no auto-send)"),
        ],
        required=True,
        default="mid_stay",
        tracking=True,
    )
    trigger_offset_hours = fields.Integer(
        default=0,
        help="Hours offset from the trigger event. "
        "E.g. post_stay + 24 = 24h after checkout.",
    )

    # --- Behavior ---------------------------------------------------------
    welcome_text = fields.Text(
        default="We'd love to hear how we're doing. Takes 1 minute.",
        translate=True,
    )
    thank_you_text = fields.Text(
        default="Thank you for your feedback!",
        translate=True,
    )
    allow_anonymous = fields.Boolean(
        default=True,
        help="Allow guests to submit without identifying themselves.",
    )
    alert_threshold = fields.Integer(
        default=2,
        help="Any score <= this triggers an instant alert to management.",
    )

    # --- Questions --------------------------------------------------------
    question_ids = fields.One2many(
        "l10n_si.feedback.question",
        "survey_id",
        string="Questions",
    )
    question_count = fields.Integer(compute="_compute_question_count")

    # --- Stats ------------------------------------------------------------
    response_ids = fields.One2many(
        "l10n_si.feedback.response",
        "survey_id",
        string="Responses",
    )
    response_count = fields.Integer(compute="_compute_response_count")
    avg_score = fields.Float(compute="_compute_response_count")
    alert_count = fields.Integer(compute="_compute_response_count")

    def _compute_question_count(self):
        for s in self:
            s.question_count = len(s.question_ids)

    def _compute_response_count(self):
        for s in self:
            responses = s.response_ids
            s.response_count = len(responses)
            scored = responses.filtered(lambda r: r.overall_score > 0)
            if scored:
                s.avg_score = sum(r.overall_score for r in scored) / len(scored)
            else:
                s.avg_score = 0.0
            s.alert_count = len(responses.filtered(lambda r: r.has_alert))

    def action_view_responses(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Responses",
            "res_model": "l10n_si.feedback.response",
            "view_mode": "tree,form",
            "domain": [("survey_id", "=", self.id)],
            "context": {"default_survey_id": self.id},
        }

    def action_preview(self):
        self.ensure_one()
        base = self.env["ir.config_parameter"].get_param(
            "web.base.url", "http://localhost:8069"
        )
        return {
            "type": "ir.actions.act_url",
            "url": f"{base}/feedback/preview/{self.id}",
            "target": "new",
        }


class FeedbackQuestion(models.Model):
    """A single question on a feedback survey."""
    _name = "l10n_si.feedback.question"
    _description = "Feedback Question"
    _order = "sequence, id"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    survey_id = fields.Many2one(
        "l10n_si.feedback.survey",
        required=True,
        ondelete="cascade",
    )
    question_type = fields.Selection(
        [
            ("rating_5", "5-star rating"),
            ("rating_10", "10-point NPS rating"),
            ("yes_no", "Yes / No"),
            ("text", "Short text"),
            ("textarea", "Long text"),
        ],
        required=True,
        default="rating_5",
    )
    is_required = fields.Boolean(default=True)
    help_text = fields.Text(translate=True)
    category = fields.Selection(
        [
            ("room", "Room"),
            ("cleanliness", "Cleanliness"),
            ("service", "Service"),
            ("breakfast", "Breakfast"),
            ("restaurant", "Restaurant"),
            ("spa", "Spa / Wellness"),
            ("staff", "Staff friendliness"),
            ("value", "Value for money"),
            ("overall", "Overall experience"),
            ("other", "Other"),
        ],
        default="overall",
        help="Used for trend analysis by category.",
    )
