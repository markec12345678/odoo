# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import secrets

from odoo import _, api, fields, models


class QuestionnaireResponse(models.Model):
    """A single guest's response to a questionnaire.

    Created when the Guest Journey emails the link. Token-authenticated.
    """
    _name = "l10n_si.questionnaire.response"
    _description = "Pre-arrival Questionnaire Response"
    _inherit = ["mail.thread"]
    _order = "create_date desc"

    name = fields.Char(compute="_compute_name", store=True)
    token = fields.Char(
        required=True,
        copy=False,
        default=lambda self: self._generate_token(),
        index=True,
    )
    template_id = fields.Many2one(
        "l10n_si.questionnaire.template",
        required=True,
        ondelete="cascade",
        tracking=True,
    )
    folio_id = fields.Many2one(
        "l10n_si.hotel.folio",
        ondelete="cascade",
        tracking=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        related="folio_id.partner_id",
        store=True,
    )
    company_id = fields.Many2one(
        related="template_id.company_id",
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
    expire_date = fields.Datetime(
        help="When the link becomes invalid (defaults to check-in date)."
    )

    # --- Captured data (structured fields for common questions) -----------
    dietary_restrictions = fields.Char(
        help="Comma-separated: vegetarian, vegan, gluten-free, halal, ..."
    )
    allergies = fields.Char(help="Comma-separated list of allergens.")
    pillow_preference = fields.Selection(
        [
            ("firm", "Firm"),
            ("soft", "Soft"),
            ("hypoallergenic", "Hypoallergenic"),
        ],
    )
    bed_configuration = fields.Selection(
        [
            ("king", "King bed"),
            ("twin", "Twin beds"),
            ("king_extra", "King + extra bed"),
            ("twin_extra", "Twin + extra bed"),
            ("crib", "Crib needed"),
        ],
    )
    floor_preference = fields.Selection(
        [
            ("low", "Low floor"),
            ("high", "High floor"),
            ("quiet", "Quiet side"),
        ],
    )
    special_occasion = fields.Selection(
        [
            ("none", "No special occasion"),
            ("birthday", "Birthday"),
            ("anniversary", "Anniversary"),
            ("honeymoon", "Honeymoon"),
            ("business", "Business trip"),
            ("family", "Family vacation"),
        ],
        default="none",
    )
    occasion_date = fields.Date()
    planned_activities = fields.Char(
        help="Comma-separated: spa, excursion, restaurant, fitness, ..."
    )
    estimated_arrival_time = fields.Char()
    transport_mode = fields.Selection(
        [
            ("car", "Car"),
            ("taxi", "Taxi"),
            ("public", "Public transport"),
            ("walk", "Walking"),
            ("other", "Other"),
        ],
    )
    parking_needed = fields.Boolean()
    communication_preference = fields.Selection(
        [
            ("email", "Email"),
            ("whatsapp", "WhatsApp"),
            ("sms", "SMS"),
            ("none", "No marketing"),
        ],
        default="email",
    )
    notes = fields.Text(string="Anything else?")

    # --- Free-form JSONB for all answers (for questions not in fields) ---
    answers_json = fields.Text(
        help="JSON-encoded dict of {question_id: answer}.",
    )

    # --- Derived ----------------------------------------------------------
    is_completed = fields.Boolean(compute="_compute_is_completed", store=True)
    days_until_checkin = fields.Integer(
        compute="_compute_days_until_checkin", store=False
    )

    # --- Constraints ------------------------------------------------------
    _sql_constraints = [
        ("token_unique", "UNIQUE(token)", "Token must be unique."),
    ]

    @api.model
    def _generate_token(self):
        return secrets.token_urlsafe(24)

    @api.depends("folio_id.name", "partner_id.name", "state")
    def _compute_name(self):
        for r in self:
            folio = r.folio_id.name or "—"
            partner = r.partner_id.name or "—"
            r.name = f"{partner} / {folio}"

    @api.depends("state")
    def _compute_is_completed(self):
        for r in self:
            r.is_completed = r.state == "completed"

    def _compute_days_until_checkin(self):
        today = fields.Date.today()
        for r in self:
            if not r.folio_id or not r.folio_id.check_in:
                r.days_until_checkin = 0
            else:
                r.days_until_checkin = (r.folio_id.check_in.date() - today).days

    # --- Public API -------------------------------------------------------
    def get_answers_dict(self):
        """Return the answers as a Python dict (parsed from JSON)."""
        self.ensure_one()
        if not self.answers_json:
            return {}
        try:
            return json.loads(self.answers_json)
        except (ValueError, TypeError):
            return {}

    def set_answer(self, question_id, value):
        """Set a single answer in the JSON store."""
        self.ensure_one()
        answers = self.get_answers_dict()
        answers[str(question_id)] = value
        self.answers_json = json.dumps(answers, ensure_ascii=False)

    def get_structured_data(self):
        """Return all captured data as a dict — used by kiosk pre-fill
        and AI Concierge context.
        """
        self.ensure_one()
        data = {
            "dietary_restrictions": self.dietary_restrictions or "",
            "allergies": self.allergies or "",
            "pillow_preference": self.pillow_preference or "",
            "bed_configuration": self.bed_configuration or "",
            "floor_preference": self.floor_preference or "",
            "special_occasion": self.special_occasion or "",
            "occasion_date": self.occasion_date.isoformat() if self.occasion_date else "",
            "planned_activities": self.planned_activities or "",
            "estimated_arrival_time": self.estimated_arrival_time or "",
            "transport_mode": self.transport_mode or "",
            "parking_needed": self.parking_needed,
            "communication_preference": self.communication_preference or "",
            "notes": self.notes or "",
        }
        # Also include any extra answers from JSON
        extra = self.get_answers_dict()
        if extra:
            data["extra_answers"] = extra
        return data

    def action_mark_started(self):
        """Guest opened the questionnaire link."""
        for r in self:
            if r.state == "sent":
                r.write(
                    {
                        "state": "started",
                        "started_date": fields.Datetime.now(),
                    }
                )

    def action_complete(self, form_data):
        """Guest submitted the questionnaire — save all data."""
        self.ensure_one()
        # Map form fields to structured fields
        structured_fields = [
            "dietary_restrictions", "allergies", "pillow_preference",
            "bed_configuration", "floor_preference", "special_occasion",
            "occasion_date", "planned_activities", "estimated_arrival_time",
            "transport_mode", "parking_needed", "communication_preference",
            "notes",
        ]
        vals = {}
        for field in structured_fields:
            if field in form_data:
                val = form_data[field]
                # Handle boolean fields
                if field == "parking_needed":
                    val = val in ("True", "true", "1", "on", True)
                vals[field] = val
        # Extra questions go to JSON
        extra = {k: v for k, v in form_data.items() if k not in structured_fields}
        if extra:
            vals["answers_json"] = json.dumps(extra, ensure_ascii=False)
        vals["state"] = "completed"
        vals["completed_date"] = fields.Datetime.now()
        self.write(vals)
        self._post_completion_message()
        return True

    def _post_completion_message(self):
        """Notify the folio chatter that the questionnaire was completed."""
        self.ensure_one()
        if not self.folio_id:
            return
        body_lines = ["<b>Pre-arrival questionnaire completed</b><ul>"]
        data = self.get_structured_data()
        if data["dietary_restrictions"]:
            body_lines.append(f"<li>Dietary: {data['dietary_restrictions']}</li>")
        if data["allergies"]:
            body_lines.append(f"<li>Allergies: {data['allergies']}</li>")
        if data["pillow_preference"]:
            body_lines.append(f"<li>Pillow: {data['pillow_preference']}</li>")
        if data["bed_configuration"]:
            body_lines.append(f"<li>Bed: {data['bed_configuration']}</li>")
        if data["special_occasion"] and data["special_occasion"] != "none":
            body_lines.append(
                f"<li>Occasion: {data['special_occasion']}"
                + (f" on {data['occasion_date']}" if data["occasion_date"] else "")
                + "</li>"
            )
        if data["planned_activities"]:
            body_lines.append(f"<li>Activities: {data['planned_activities']}</li>")
        if data["estimated_arrival_time"]:
            body_lines.append(f"<li>Arrival: {data['estimated_arrival_time']}</li>")
        if data["transport_mode"]:
            body_lines.append(f"<li>Transport: {data['transport_mode']}</li>")
        if data["parking_needed"]:
            body_lines.append("<li>Parking: <b>YES</b></li>")
        if data["notes"]:
            body_lines.append(f"<li>Notes: {data['notes']}</li>")
        body_lines.append("</ul>")
        self.folio_id.message_post(
            body="".join(body_lines),
            subject=_("Pre-arrival questionnaire completed"),
        )

    def action_expire(self):
        """Mark as expired (e.g. check-in date has passed)."""
        for r in self:
            if r.state not in ("completed", "expired"):
                r.state = "expired"

    def _send_link_email(self):
        """Send the questionnaire link to the guest via email."""
        self.ensure_one()
        if not self.partner_id or not self.partner_id.email:
            return False
        base_url = self.env["ir.config_parameter"].get_param(
            "web.base.url", "http://localhost:8069"
        )
        link = f"{base_url}/questionnaire/start/{self.token}"
        # Use Odoo's mail template system — render via Jinja
        subject = _(
            "Help us prepare your stay at %(hotel)s",
            hotel=self.folio_id.company_id.name or "our hotel",
        )
        body_html = f"""
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
  <h2 style="color: #875A7B;">Hi {self.partner_id.name or 'there'},</h2>
  <p>We're excited to welcome you on <b>{self.folio_id.check_in.strftime('%d.%m.%Y') if self.folio_id.check_in else 'your upcoming stay'}</b>.</p>
  <p>To make your stay perfect, please take {self.template_id.estimated_minutes or 3} minutes to fill out our short pre-arrival questionnaire. It covers:</p>
  <ul>
    <li>Dietary preferences &amp; allergies</li>
    <li>Room &amp; pillow preferences</li>
    <li>Planned activities &amp; special occasions</li>
    <li>Arrival details</li>
  </ul>
  <p style="margin: 30px 0;">
    <a href="{link}"
       style="background: #875A7B; color: white; padding: 14px 28px;
              text-decoration: none; border-radius: 6px; font-size: 16px;">
      Start questionnaire
    </a>
  </p>
  <p style="color: #888; font-size: 12px;">
    This link is personal to you. No login required.
  </p>
</div>
"""
        mail = self.env["mail.mail"].create(
            {
                "subject": subject,
                "body_html": body_html,
                "email_from": self.company_id.email or "noreply@example.com",
                "email_to": self.partner_id.email,
                "author_id": self.env.user.partner_id.id,
                "model": "l10n_si.questionnaire.response",
                "res_id": self.id,
            }
        )
        mail.send(raise_exception=False)
        return True

    # --- Cron -------------------------------------------------------------
    @api.model
    def _cron_expire_stale_responses(self):
        """Expire responses whose folio check-in has passed."""
        today = fields.Datetime.now()
        stale = self.search(
            [
                ("state", "in", ["sent", "started"]),
                ("folio_id.check_in", "<", today),
            ]
        )
        stale.action_expire()
