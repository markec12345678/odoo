# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class FeedbackAlert(models.Model):
    """An alert triggered by a low feedback score.

    Each alert can be assigned, investigated, and resolved with an action.
    """
    _name = "l10n_si.feedback.alert"
    _description = "Guest Feedback Alert"
    _inherit = ["mail.thread"]
    _order = "create_date desc"

    name = fields.Char(compute="_compute_name", store=True)
    response_id = fields.Many2one(
        "l10n_si.feedback.response",
        required=True,
        ondelete="cascade",
        tracking=True,
    )
    survey_id = fields.Many2one(
        related="response_id.survey_id",
        store=True,
    )
    folio_id = fields.Many2one(
        related="response_id.folio_id",
        store=True,
    )
    partner_id = fields.Many2one(
        related="response_id.partner_id",
        store=True,
    )
    company_id = fields.Many2one(
        related="response_id.company_id",
        store=True,
    )
    question_id = fields.Many2one(
        "l10n_si.feedback.question",
        required=True,
        ondelete="cascade",
    )
    score = fields.Integer(required=True, help="The low score that triggered this alert.")
    comment = fields.Text(help="Free-text comment from the guest, if any.")
    category = fields.Selection(
        related="question_id.category",
        store=True,
    )

    # --- State ------------------------------------------------------------
    state = fields.Selection(
        [
            ("open", "Open"),
            ("acknowledged", "Acknowledged"),
            ("in_progress", "In Progress"),
            ("resolved", "Resolved"),
            ("wont_fix", "Won't Fix"),
        ],
        default="open",
        required=True,
        tracking=True,
    )
    assigned_to = fields.Many2one("res.users", tracking=True)
    acknowledged_on = fields.Datetime(readonly=True)
    resolved_on = fields.Datetime(readonly=True)

    # --- Action -----------------------------------------------------------
    action_taken = fields.Text(
        help="What action was taken to resolve this issue?",
    )
    root_cause = fields.Text(
        help="What was the root cause of this low score?",
    )
    follow_up_done = fields.Boolean(
        default=False,
        help="Has the guest been contacted about this issue?",
    )

    @api.depends("question_id.name", "partner_id.name", "score")
    def _compute_name(self):
        for a in self:
            partner = a.partner_id.name if a.partner_id else "Anonymous"
            question = a.question_id.name or ""
            a.name = f"{partner} — {question} ({a.score}/5)"

    def action_acknowledge(self):
        for a in self:
            if a.state != "open":
                continue
            a.write(
                {
                    "state": "acknowledged",
                    "acknowledged_on": fields.Datetime.now(),
                    "assigned_to": self.env.user.id,
                }
            )

    def action_start_progress(self):
        for a in self:
            if a.state not in ("open", "acknowledged"):
                continue
            a.write(
                {
                    "state": "in_progress",
                    "assigned_to": a.assigned_to.id or self.env.user.id,
                }
            )

    def action_resolve(self):
        for a in self:
            if a.state not in ("acknowledged", "in_progress"):
                continue
            a.write(
                {
                    "state": "resolved",
                    "resolved_on": fields.Datetime.now(),
                }
            )

    def action_wont_fix(self):
        for a in self:
            if a.state == "resolved":
                continue
            a.write(
                {
                    "state": "wont_fix",
                    "resolved_on": fields.Datetime.now(),
                }
            )
