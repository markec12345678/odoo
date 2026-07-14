# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class QuestionnaireTemplate(models.Model):
    """A reusable questionnaire definition — the questions guests answer.

    A template groups questions into sections (Dietary, Room, Activities, ...).
    Each hotel can have multiple templates (one per season, one per property).
    """
    _name = "l10n_si.questionnaire.template"
    _description = "Pre-arrival Questionnaire Template"
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

    # --- Behavior ---------------------------------------------------------
    welcome_text = fields.Text(
        default="Help us prepare your perfect stay by answering a few questions.",
        translate=True,
    )
    thank_you_text = fields.Text(
        default="Thank you! Your preferences have been saved. "
        "We look forward to welcoming you.",
        translate=True,
    )
    estimated_minutes = fields.Integer(
        default=3,
        help="Estimated time to complete the questionnaire.",
    )

    # --- Sections ---------------------------------------------------------
    section_ids = fields.One2many(
        "l10n_si.questionnaire.section",
        "template_id",
        string="Sections",
    )

    # --- Stats ------------------------------------------------------------
    response_ids = fields.One2many(
        "l10n_si.questionnaire.response", "template_id", string="Responses"
    )
    response_count = fields.Integer(compute="_compute_response_count")
    completed_count = fields.Integer(compute="_compute_response_count")

    def _compute_response_count(self):
        for tmpl in self:
            responses = tmpl.response_ids
            tmpl.response_count = len(responses)
            tmpl.completed_count = len(
                responses.filtered(lambda r: r.state == "completed")
            )

    def action_view_responses(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Responses",
            "res_model": "l10n_si.questionnaire.response",
            "view_mode": "tree,form",
            "domain": [("template_id", "=", self.id)],
            "context": {"default_template_id": self.id},
        }

    def action_preview(self):
        """Open the questionnaire in preview mode."""
        self.ensure_one()
        base = self.env["ir.config_parameter"].get_param(
            "web.base.url", "http://localhost:8069"
        )
        return {
            "type": "ir.actions.act_url",
            "url": f"{base}/questionnaire/preview/{self.id}",
            "target": "new",
        }


class QuestionnaireSection(models.Model):
    """A section of questions, e.g. 'Dietary preferences'."""
    _name = "l10n_si.questionnaire.section"
    _description = "Questionnaire Section"
    _order = "sequence, id"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    template_id = fields.Many2one(
        "l10n_si.questionnaire.template",
        required=True,
        ondelete="cascade",
    )
    description = fields.Text(translate=True)
    question_ids = fields.One2many(
        "l10n_si.questionnaire.question", "section_id", string="Questions"
    )
    question_count = fields.Integer(compute="_compute_question_count")

    def _compute_question_count(self):
        for s in self:
            s.question_count = len(s.question_ids)


class QuestionnaireQuestion(models.Model):
    """A single question on the questionnaire."""
    _name = "l10n_si.questionnaire.question"
    _description = "Questionnaire Question"
    _order = "sequence, id"

    name = fields.Char(required=True, translate=True, string="Question Text")
    sequence = fields.Integer(default=10)
    section_id = fields.Many2one(
        "l10n_si.questionnaire.section",
        required=True,
        ondelete="cascade",
    )
    template_id = fields.Many2one(
        related="section_id.template_id",
        store=True,
    )
    question_type = fields.Selection(
        [
            ("text", "Short text"),
            ("textarea", "Long text"),
            ("single_select", "Single choice (dropdown)"),
            ("multi_select", "Multiple choice (checkboxes)"),
            ("date", "Date"),
            ("time", "Time"),
            ("integer", "Number"),
            ("boolean", "Yes / No"),
            ("rating", "Rating (1-5 stars)"),
        ],
        required=True,
        default="text",
    )
    is_required = fields.Boolean(default=False)
    help_text = fields.Text(translate=True)
    # Comma-separated options for single_select / multi_select
    options_raw = fields.Text(
        string="Options (one per line)",
        help="One option per line. Used for single_select and multi_select.",
    )
    # Field on response where this answer is stored (for structured queries)
    storage_field = fields.Char(
        help="Technical name of the field on l10n_si.questionnaire.response "
        "where this answer is stored (optional). If left empty, the answer "
        "is stored in the JSONB 'answers' field.",
    )

    def get_options(self):
        """Return list of option strings."""
        if not self.options_raw:
            return []
        return [line.strip() for line in self.options_raw.split("\n") if line.strip()]
