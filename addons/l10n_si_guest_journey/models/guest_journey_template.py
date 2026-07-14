# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class GuestJourneyTemplate(models.Model):
    """Reusable template that defines what to send to guests at a specific
    point in their journey.

    A template specifies:
      * The stage (pre_arrival / in_stay / post_stay)
      * When to fire (offset days + reference event: check_in or check_out)
      * The channel (email / whatsapp)
      * The language (or 'all' for any)
      * The Jinja-rendered subject and body
      * Whether AI Core should personalise the body further before sending
    """
    _name = "l10n_si.guest.journey.template"
    _description = "Guest Journey Communication Template"
    _inherit = ["mail.thread"]
    _order = "stage, offset_days, sequence, id"

    name = fields.Char(required=True, tracking=True, translate=True)
    active = fields.Boolean(default=True, tracking=True)
    sequence = fields.Integer(default=10)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,
    )

    # --- Trigger -----------------------------------------------------------
    stage = fields.Selection(
        [
            ("pre_arrival", "Pre-arrival"),
            ("in_stay", "In-stay"),
            ("post_stay", "Post-stay"),
        ],
        required=True,
        default="pre_arrival",
        tracking=True,
    )
    trigger_event = fields.Selection(
        [
            ("check_in", "Check-in date"),
            ("check_out", "Check-out date"),
        ],
        required=True,
        default="check_in",
        help="Reference date used to compute the scheduled date.",
    )
    offset_days = fields.Integer(
        required=True,
        default=-1,
        help="Days relative to the trigger event. "
        "Negative = before, 0 = same day, positive = after.",
    )
    send_hour = fields.Integer(
        default=9,
        help="Hour of day (0-23) when the message should be sent, in the "
        "hotel's timezone.",
    )
    send_minute = fields.Integer(default=0)

    # --- Channel & audience ------------------------------------------------
    channel = fields.Selection(
        [
            ("email", "Email"),
            ("whatsapp", "WhatsApp"),
        ],
        required=True,
        default="email",
    )
    lang_id = fields.Many2one(
        "res.lang",
        string="Language",
        help="Leave empty to apply to all languages "
        "(lowest sequence template wins).",
    )

    # --- Content -----------------------------------------------------------
    subject = fields.Char(
        required=True,
        tracking=True,
        translate=True,
        help="Jinja2-rendered. Available variables: guest_name, "
        "guest_first_name, room, check_in, check_out, hotel_name, "
        "nights, adults, folio, partner.",
    )
    body_html = fields.Html(required=True, translate=True, sanitize=True)
    ai_personalize = fields.Boolean(
        default=False,
        help="If set, AI Core will rewrite the body to be more personal "
        "(adds guest's name, weather, local tips based on stay history).",
    )
    ai_task_type = fields.Selection(
        [
            ("multilingual", "Multilingual"),
            ("creative", "Creative"),
            ("general", "General"),
        ],
        default="creative",
        help="Routing hint for AI Core when personalising.",
    )

    # --- Stats -------------------------------------------------------------
    step_ids = fields.One2many(
        "l10n_si.guest.journey.step", "template_id", string="Generated Steps"
    )
    step_count = fields.Integer(compute="_compute_step_count")
    sent_count = fields.Integer(compute="_compute_step_count")
    failed_count = fields.Integer(compute="_compute_step_count")

    # --- Constraints -------------------------------------------------------
    _sql_constraints = [
        (
            "offset_range_check",
            "CHECK (offset_days BETWEEN -30 AND 30)",
            "Offset days must be between -30 and +30.",
        ),
        (
            "hour_range_check",
            "CHECK (send_hour BETWEEN 0 AND 23)",
            "Send hour must be between 0 and 23.",
        ),
        (
            "minute_range_check",
            "CHECK (send_minute BETWEEN 0 AND 59)",
            "Send minute must be between 0 and 59.",
        ),
    ]

    @api.depends("step_ids.state")
    def _compute_step_count(self):
        step_data = self.env["l10n_si.guest.journey.step"].read_group(
            [("template_id", "in", self.ids)],
            ["template_id", "state"],
            ["template_id", "state"],
            lazy=False,
        )
        counts = {t.id: {"total": 0, "sent": 0, "failed": 0} for t in self}
        for row in step_data:
            tid = row["template_id"][0]
            state = row["state"]
            counts[tid]["total"] += row["__count"]
            if state == "sent":
                counts[tid]["sent"] += row["__count"]
            elif state == "failed":
                counts[tid]["failed"] += row["__count"]
        for tmpl in self:
            tmpl.step_count = counts[tmpl.id]["total"]
            tmpl.sent_count = counts[tmpl.id]["sent"]
            tmpl.failed_count = counts[tmpl.id]["failed"]

    # --- Helpers -----------------------------------------------------------
    def _get_render_context(self, folio):
        """Build the Jinja context used to render subject/body."""
        partner = folio.partner_id
        first_name = (partner.name or "").split(" ")[0]
        # Find main room from reservation lines
        room_name = ""
        reservation = self.env["l10n_si.hotel.reservation"].search(
            [("folio_id", "=", folio.id)], limit=1
        )
        if reservation and reservation.room_id:
            room_name = reservation.room_id.name or ""
        hotel = folio.company_id or self.env.company
        # Compute nights from check_in/check_out (both Datetime)
        nights = 0
        if folio.check_in and folio.check_out:
            nights = max(
                0,
                (folio.check_out.date() - folio.check_in.date()).days,
            )
        check_in_str = (
            fields.Date.to_string(folio.check_in.date())
            if folio.check_in else ""
        )
        check_out_str = (
            fields.Date.to_string(folio.check_out.date())
            if folio.check_out else ""
        )
        return {
            "guest_name": partner.name or "",
            "guest_first_name": first_name,
            "guest_email": partner.email or "",
            "guest_phone": partner.mobile or partner.phone or "",
            "room": room_name,
            "check_in": check_in_str,
            "check_out": check_out_str,
            "nights": nights,
            "adults": folio.adults or 0,
            "children": folio.children or 0,
            "hotel_name": hotel.name or "",
            "hotel_phone": hotel.phone or "",
            "hotel_email": hotel.email or "",
            "partner": partner,
            "folio": folio,
        }

    def render_subject(self, folio):
        self.ensure_one()
        try:
            return safe_eval(
                "render(subject, dict(context))",
                {
                    "render": self.env["mail.render.mixin"]._render_template,
                    "subject": self.subject,
                    "context": self._get_render_context(folio),
                },
                mode="exec",
            ) or self.subject
        except Exception:
            return self.subject

    def render_body(self, folio):
        self.ensure_one()
        try:
            ctx = self._get_render_context(folio)
            return self.env["mail.render.mixin"]._render_template(
                self.body_html, ctx
            ) or self.body_html
        except Exception:
            return self.body_html

    def action_view_steps(self):
        """Open the steps generated from this template."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Steps",
            "res_model": "l10n_si.guest.journey.step",
            "view_mode": "kanban,tree,form",
            "domain": [("template_id", "=", self.id)],
            "context": {"default_template_id": self.id},
        }

    def action_test_render(self):
        """Open a wizard showing a rendered preview of subject + body
        using the most recent confirmed folio in the company, or create a
        transient preview record.
        """
        self.ensure_one()
        folio = self.env["l10n_si.hotel.folio"].search(
            [
                ("company_id", "=", self.env.company.id),
                ("partner_id", "!=", False),
            ],
            order="checkin_date desc",
            limit=1,
        )
        if not folio:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "No folio found",
                    "message": "Create at least one folio with a partner to preview the template.",
                    "type": "warning",
                },
            }
        subject = self.render_subject(folio)
        body = self.render_body(folio)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": subject,
                "message": body,
                "type": "info",
                "sticky": True,
            },
        }

    def _compute_scheduled_date(self, folio):
        """Compute the scheduled datetime for this template applied to folio."""
        self.ensure_one()
        ref_dt = (
            folio.check_in if self.trigger_event == "check_in" else folio.check_out
        )
        if not ref_dt:
            return False
        from datetime import datetime, timedelta

        ref_date = ref_dt.date()
        target = datetime(
            ref_date.year, ref_date.month, ref_date.day,
            self.send_hour, self.send_minute, 0,
        )
        # offset_days is signed; subtract positive to go back in time
        return target - timedelta(days=-self.offset_days)
