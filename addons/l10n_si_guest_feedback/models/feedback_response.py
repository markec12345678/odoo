# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import secrets

from odoo import _, api, fields, models


class FeedbackResponse(models.Model):
    """A single guest's feedback response.

    Token-authenticated — guests don't need to log in.
    """
    _name = "l10n_si.feedback.response"
    _description = "Guest Feedback Response"
    _inherit = ["mail.thread"]
    _order = "create_date desc"

    name = fields.Char(compute="_compute_name", store=True)
    token = fields.Char(
        required=True,
        copy=False,
        default=lambda self: self._generate_token(),
        index=True,
    )
    survey_id = fields.Many2one(
        "l10n_si.feedback.survey",
        required=True,
        ondelete="cascade",
        tracking=True,
    )
    folio_id = fields.Many2one(
        "l10n_si.hotel.folio",
        ondelete="set null",
        tracking=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        related="folio_id.partner_id",
        store=True,
    )
    company_id = fields.Many2one(
        related="survey_id.company_id",
        store=True,
    )

    # --- State ------------------------------------------------------------
    state = fields.Selection(
        [
            ("sent", "Link sent"),
            ("started", "Started"),
            ("completed", "Completed"),
            ("expired", "Expired"),
        ],
        default="sent",
        required=True,
        tracking=True,
    )
    sent_date = fields.Datetime(default=fields.Datetime.now)
    started_date = fields.Datetime()
    completed_date = fields.Datetime()
    is_anonymous = fields.Boolean(default=False)

    # --- Answers (JSON: {question_id: {score, text}}) --------------------
    answers_json = fields.Text()
    overall_score = fields.Float(
        compute="_compute_overall_score",
        store=True,
        help="Average of all numeric answers (1-5 scale).",
    )
    nps_score = fields.Integer(
        help="NPS score 0-10 if the survey includes an NPS question.",
    )
    has_alert = fields.Boolean(
        compute="_compute_has_alert",
        store=True,
        help="True if any score is <= the survey's alert threshold.",
    )
    alert_ids = fields.One2many(
        "l10n_si.feedback.alert",
        "response_id",
        string="Alerts",
    )

    # --- AI ---------------------------------------------------------------
    sentiment = fields.Selection(
        [
            ("positive", "Positive"),
            ("neutral", "Neutral"),
            ("negative", "Negative"),
        ],
        readonly=True,
    )
    sentiment_summary = fields.Text(readonly=True)

    # --- Constraints ------------------------------------------------------
    _sql_constraints = [
        ("token_unique", "UNIQUE(token)", "Token must be unique."),
    ]

    @api.model
    def _generate_token(self):
        return secrets.token_urlsafe(24)

    @api.depends("folio_id.name", "partner_id.name", "create_date", "state")
    def _compute_name(self):
        for r in self:
            partner = r.partner_id.name if r.partner_id else "Anonymous"
            folio = r.folio_id.name if r.folio_id else "—"
            r.name = f"{partner} / {folio}"

    @api.depends("answers_json")
    def _compute_overall_score(self):
        for r in self:
            answers = r.get_answers_dict()
            scores = [
                a.get("score", 0)
                for a in answers.values()
                if isinstance(a.get("score"), (int, float)) and a.get("score") > 0
            ]
            if scores:
                # Normalize 1-10 scores to 1-5
                normalized = [s / 2 if s > 5 else s for s in scores]
                r.overall_score = round(sum(normalized) / len(normalized), 2)
            else:
                r.overall_score = 0.0

    @api.depends("answers_json", "survey_id.alert_threshold")
    def _compute_has_alert(self):
        for r in self:
            answers = r.get_answers_dict()
            threshold = r.survey_id.alert_threshold or 2
            has_alert = False
            for a in answers.values():
                score = a.get("score", 0)
                if isinstance(score, (int, float)) and 0 < score <= threshold:
                    has_alert = True
                    break
            r.has_alert = has_alert

    # --- Public API -------------------------------------------------------
    def get_answers_dict(self):
        self.ensure_one()
        if not self.answers_json:
            return {}
        try:
            return json.loads(self.answers_json)
        except (ValueError, TypeError):
            return {}

    def set_answer(self, question_id, score=None, text=None):
        self.ensure_one()
        answers = self.get_answers_dict()
        key = str(question_id)
        existing = answers.get(key, {})
        if score is not None:
            existing["score"] = score
        if text is not None:
            existing["text"] = text
        answers[key] = existing
        self.answers_json = json.dumps(answers, ensure_ascii=False)

    def action_mark_started(self):
        for r in self:
            if r.state == "sent":
                r.write(
                    {
                        "state": "started",
                        "started_date": fields.Datetime.now(),
                    }
                )

    def action_complete(self, form_data):
        """Guest submitted the feedback — save all answers."""
        self.ensure_one()
        threshold = self.survey_id.alert_threshold or 2
        for question in self.survey_id.question_ids:
            key = f"q_{question.id}"
            value = form_data.get(key)
            if value is None or value == "":
                continue
            if question.question_type in ("rating_5", "rating_10", "yes_no"):
                try:
                    score = int(value)
                except (ValueError, TypeError):
                    continue
                self.set_answer(question.id, score=score)
                if question.question_type == "rating_10":
                    self.nps_score = score
            else:
                self.set_answer(question.id, text=value)
        self.write(
            {
                "state": "completed",
                "completed_date": fields.Datetime.now(),
            }
        )
        # Trigger alert if any low score
        if self.has_alert:
            self._create_alerts()
        # Optional AI sentiment analysis
        self._run_sentiment_analysis()
        # Post to folio chatter
        self._post_to_folio()
        return True

    def _create_alerts(self):
        """Create alert records for each low-scored question."""
        self.ensure_one()
        answers = self.get_answers_dict()
        threshold = self.survey_id.alert_threshold or 2
        for question in self.survey_id.question_ids:
            key = str(question.id)
            answer = answers.get(key, {})
            score = answer.get("score", 0)
            if isinstance(score, (int, float)) and 0 < score <= threshold:
                self.env["l10n_si.feedback.alert"].create(
                    {
                        "response_id": self.id,
                        "question_id": question.id,
                        "score": score,
                        "comment": answer.get("text", ""),
                        "category": question.category,
                        "state": "open",
                    }
                )
        # Send instant notifications
        self._send_alert_notifications()

    def _send_alert_notifications(self):
        """Send instant alerts via email, WhatsApp, and internal chat."""
        self.ensure_one()
        if not self.has_alert:
            return
        # Email to company managers
        managers = self.env["res.users"].search(
            [
                ("groups_id", "in", [self.env.ref("l10n_si_hotel.hotel_manager_group").id]),
                ("company_ids", "in", [self.company_id.id]),
                ("notification_type", "=", "email"),
            ]
        )
        for manager in managers:
            self.env["mail.mail"].create(
                {
                    "subject": _(
                        "⚠️ LOW FEEDBACK ALERT — %(guest)s (%(score).1f/5)",
                        guest=self.partner_id.name or "Anonymous",
                        score=self.overall_score,
                    ),
                    "body_html": self._get_alert_email_body(),
                    "email_from": self.company_id.email or "noreply@example.com",
                    "email_to": manager.email,
                    "author_id": self.env.user.partner_id.id,
                    "model": "l10n_si.feedback.response",
                    "res_id": self.id,
                }
            ).send(raise_exception=False)
        # Internal chatter message
        if self.folio_id:
            self.folio_id.message_post(
                body=self._get_alert_email_body(),
                subject=_("⚠️ Low feedback score received"),
                partner_ids=managers.mapped("partner_id").ids,
            )

    def _get_alert_email_body(self):
        """Build the HTML body for alert emails."""
        self.ensure_one()
        answers = self.get_answers_dict()
        body = [
            '<div style="font-family: Arial, sans-serif; max-width: 600px; color: #333;">',
            '<h2 style="color: #dc3545;">⚠️ Low Feedback Score Alert</h2>',
            f'<p><strong>Guest:</strong> {self.partner_id.name or "Anonymous"}</p>',
            f'<p><strong>Folio:</strong> {self.folio_id.name or "—"}</p>',
            f'<p><strong>Overall score:</strong> {self.overall_score:.1f}/5</p>',
            '<h3 style="color: #dc3545;">Low-scored questions:</h3>',
            '<ul>',
        ]
        threshold = self.survey_id.alert_threshold or 2
        for question in self.survey_id.question_ids:
            answer = answers.get(str(question.id), {})
            score = answer.get("score", 0)
            if isinstance(score, (int, float)) and 0 < score <= threshold:
                body.append(
                    f'<li><strong>{question.name}</strong>: '
                    f'{score}/5'
                    f'{" — " + answer.get("text", "") if answer.get("text") else ""}'
                    f'</li>'
                )
        body.append("</ul>")
        body.append(
            f'<p style="margin-top: 20px;">'
            f'<a href="/web#model=l10n_si.feedback.response&amp;id={self.id}" '
            f'style="background: #dc3545; color: white; padding: 10px 20px; '
            f'text-decoration: none; border-radius: 4px;">View in Odoo</a>'
            f'</p>'
        )
        body.append("</div>")
        return "".join(body)

    def _run_sentiment_analysis(self):
        """Use AI Core to analyze the sentiment of free-text answers."""
        self.ensure_one()
        ai_module = self.env["ir.module.module"].search(
            [("name", "=", "l10n_si_ai_core"), ("state", "=", "installed")],
            limit=1,
        )
        if not ai_module:
            return
        # Gather all text answers
        answers = self.get_answers_dict()
        text_parts = []
        for question in self.survey_id.question_ids:
            answer = answers.get(str(question.id), {})
            text = answer.get("text", "")
            if text:
                text_parts.append(f"{question.name}: {text}")
        if not text_parts:
            return
        prompt = (
            "Analyze the sentiment of these guest feedback comments. "
            "Output a single word: positive, neutral, or negative. "
            "Then on a new line, write a 1-sentence summary.\n\n"
            + "\n".join(text_parts)
        )
        try:
            result = self.env["l10n_si.ai.core"].generate(
                prompt=prompt,
                task_type="multilingual",
                max_tokens=200,
            )
            text = result.get("text", "") if isinstance(result, dict) else ""
            if text:
                lines = text.strip().split("\n", 1)
                sentiment_word = lines[0].lower().strip()
                if "positive" in sentiment_word:
                    sentiment = "positive"
                elif "negative" in sentiment_word:
                    sentiment = "negative"
                else:
                    sentiment = "neutral"
                summary = lines[1].strip() if len(lines) > 1 else ""
                self.write(
                    {
                        "sentiment": sentiment,
                        "sentiment_summary": summary[:500],
                    }
                )
        except Exception:  # noqa: BLE001
            pass

    def _post_to_folio(self):
        """Post a summary to the folio chatter."""
        self.ensure_one()
        if not self.folio_id:
            return
        body = (
            f"<b>Feedback received</b> — Overall score: "
            f"<b>{self.overall_score:.1f}/5</b>"
        )
        if self.sentiment:
            body += f" (sentiment: {self.sentiment})"
        if self.has_alert:
            body += ' <span style="color: #dc3545;">⚠️ LOW SCORE ALERT</span>'
        self.folio_id.message_post(
            body=body,
            subject=_("Guest feedback received"),
        )

    def _send_link_email(self):
        """Send the feedback link to the guest via email."""
        self.ensure_one()
        if not self.partner_id or not self.partner_id.email:
            return False
        base_url = self.env["ir.config_parameter"].get_param(
            "web.base.url", "http://localhost:8069"
        )
        link = f"{base_url}/feedback/start/{self.token}"
        subject = _(
            "How are we doing? — %(hotel)s",
            hotel=self.folio_id.company_id.name or "our hotel",
        )
        body_html = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
  <h2 style="color: #875A7B;">Hi {self.partner_id.name or 'there'},</h2>
  <p>{self.survey_id.welcome_text or "We'd love your feedback."}</p>
  <p>It takes less than 1 minute.</p>
  <p style="margin: 30px 0;">
    <a href="{link}"
       style="background: #875A7B; color: white; padding: 14px 28px;
              text-decoration: none; border-radius: 6px; font-size: 16px;">
      Give feedback
    </a>
  </p>
  <p style="color: #888; font-size: 12px;">
    No login required. This link is personal to you.
  </p>
</div>
"""
        self.env["mail.mail"].create(
            {
                "subject": subject,
                "body_html": body_html,
                "email_from": self.company_id.email or "noreply@example.com",
                "email_to": self.partner_id.email,
                "author_id": self.env.user.partner_id.id,
                "model": "l10n_si.feedback.response",
                "res_id": self.id,
            }
        ).send(raise_exception=False)
        return True

    # --- Cron -------------------------------------------------------------
    @api.model
    def _cron_expire_stale(self):
        """Expire responses that were sent but never completed
        (older than 7 days).
        """
        from datetime import timedelta

        cutoff = fields.Datetime.now() - timedelta(days=7)
        stale = self.search(
            [
                ("state", "in", ["sent", "started"]),
                ("sent_date", "<", cutoff),
            ]
        )
        stale.write({"state": "expired"})
