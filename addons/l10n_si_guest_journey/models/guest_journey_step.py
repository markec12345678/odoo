# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class GuestJourneyStep(models.Model):
    """Concrete instance of a journey template scheduled for a specific folio.

    Steps are created when the receptionist (or automation) clicks
    "Generate journey" on a folio. They can be sent manually or by cron.
    """
    _name = "l10n_si.guest.journey.step"
    _description = "Guest Journey Step"
    _inherit = ["mail.thread"]
    _order = "scheduled_date, id"

    name = fields.Char(compute="_compute_name", store=True)
    folio_id = fields.Many2one(
        "l10n_si.hotel.folio",
        required=True,
        ondelete="cascade",
        tracking=True,
    )
    template_id = fields.Many2one(
        "l10n_si.guest.journey.template",
        required=True,
        ondelete="restrict",
        tracking=True,
    )
    partner_id = fields.Many2one(
        related="folio_id.partner_id",
        store=True,
    )
    company_id = fields.Many2one(
        related="folio_id.company_id",
        store=True,
    )

    # --- Scheduling --------------------------------------------------------
    scheduled_date = fields.Datetime(
        required=True,
        tracking=True,
        help="When this step should be sent.",
    )
    sent_date = fields.Datetime(tracking=True)
    state = fields.Selection(
        [
            ("scheduled", "Scheduled"),
            ("sent", "Sent"),
            ("failed", "Failed"),
            ("skipped", "Skipped"),
        ],
        default="scheduled",
        required=True,
        tracking=True,
    )
    skip_reason = fields.Char()

    # --- Content snapshot --------------------------------------------------
    channel = fields.Selection(related="template_id.channel", store=True)
    stage = fields.Selection(related="template_id.stage", store=True)
    subject = fields.Char()
    body_html = fields.Html()
    mail_message_id = fields.Many2one("mail.mail", string="Mail Reference")
    whatsapp_message_id = fields.Char(string="WhatsApp Message ID")

    error_message = fields.Text()

    # --- Computed ----------------------------------------------------------
    @api.depends("template_id.name", "folio_id.name", "scheduled_date")
    def _compute_name(self):
        for step in self:
            tmpl = step.template_id.name or ""
            folio = step.folio_id.name or ""
            step.name = f"{tmpl} — {folio}"

    # --- Actions -----------------------------------------------------------
    def action_send_now(self):
        """Force-send all selected scheduled/failed steps immediately."""
        for step in self:
            if step.state == "sent":
                continue
            step._send()

    def action_skip(self, reason=""):
        for step in self:
            if step.state != "scheduled":
                continue
            step.write(
                {
                    "state": "skipped",
                    "skip_reason": reason or "Manually skipped",
                }
            )

    def action_retry(self):
        failed = self.filtered(lambda s: s.state == "failed")
        failed.write({"state": "scheduled", "error_message": False})
        failed._send()

    # --- Core sending ------------------------------------------------------
    def _send(self):
        """Send the step via the configured channel. Idempotent."""
        for step in self:
            if step.state == "sent":
                continue
            try:
                # Re-render in case context changed (e.g. room upgrade)
                ctx = step.template_id._get_render_context(step.folio_id)
                subject = (
                    step.env["mail.render.mixin"]
                    ._render_template(step.template_id.subject, ctx)
                    or step.template_id.subject
                )
                body = (
                    step.env["mail.render.mixin"]
                    ._render_template(step.template_id.body_html, ctx)
                    or step.template_id.body_html
                )
                # Optional AI personalisation
                if step.template_id.ai_personalize:
                    personalised = step._ai_personalize(body, step.folio_id)
                    if personalised:
                        body = personalised

                step.write(
                    {
                        "subject": subject,
                        "body_html": body,
                    }
                )

                if step.channel == "whatsapp":
                    ref = step._send_via_whatsapp(body)
                    step.write(
                        {
                            "whatsapp_message_id": ref or "",
                            "state": "sent",
                            "sent_date": fields.Datetime.now(),
                            "error_message": False,
                        }
                    )
                else:
                    mail = step._send_via_email(subject, body)
                    step.write(
                        {
                            "mail_message_id": mail.id if mail else False,
                            "state": "sent",
                            "sent_date": fields.Datetime.now(),
                            "error_message": False,
                        }
                    )
            except Exception as e:  # noqa: BLE001
                step.write(
                    {
                        "state": "failed",
                        "error_message": str(e)[:500],
                    }
                )

    def _send_via_email(self, subject, body):
        """Send via Odoo's mail.mail. Returns the mail record."""
        self.ensure_one()
        if not self.partner_id.email:
            raise UserError(_("Guest has no email address."))
        mail = self.env["mail.mail"].create(
            {
                "subject": subject,
                "body_html": body,
                "email_from": self.company_id.email or "noreply@example.com",
                "email_to": self.partner_id.email,
                "author_id": self.env.user.partner_id.id,
                "model": "l10n_si.hotel.folio",
                "res_id": self.folio_id.id,
            }
        )
        mail.send(raise_exception=False)
        return mail

    def _send_via_whatsapp(self, body):
        """Send via WhatsApp Business Cloud API if module is installed.
        Falls back to email if WhatsApp module is not available.
        """
        self.ensure_one()
        wa_module = self.env["ir.module.module"].search(
            [("name", "=", "l10n_si_whatsapp_business"), ("state", "=", "installed")],
            limit=1,
        )
        if not wa_module:
            # Fallback: try via email
            return self._send_via_email("WhatsApp (fallback)", body).id

        if not self.partner_id.mobile:
            raise UserError(_("Guest has no mobile number for WhatsApp."))
        # Strip HTML to plain text for WhatsApp
        plain = self.env["mail.render.mixin"]._strip_html(body) if hasattr(
            self.env["mail.render.mixin"], "_strip_html"
        ) else body
        # Look up WhatsApp account
        wa_account = self.env["l10n_si.whatsapp.account"].search(
            [("company_id", "=", self.company_id.id), ("active", "=", True)],
            limit=1,
        )
        if not wa_account:
            raise UserError(_("No active WhatsApp account for this company."))
        msg = self.env["l10n_si.whatsapp.message"].create(
            {
                "account_id": wa_account.id,
                "partner_id": self.partner_id.id,
                "body": plain,
                "direction": "outbound",
                "state": "queued",
            }
        )
        msg._send()
        return msg.wa_message_id or msg.id

    def _ai_personalize(self, body, folio):
        """Use AI Core to enrich the body. Returns enriched body or False."""
        self.ensure_one()
        ai_core = self.env["ir.module.module"].search(
            [("name", "=", "l10n_si_ai_core"), ("state", "=", "installed")],
            limit=1,
        )
        if not ai_core:
            return False
        try:
            partner = folio.partner_id
            check_in_str = folio.check_in.strftime("%Y-%m-%d") if folio.check_in else "?"
            check_out_str = folio.check_out.strftime("%Y-%m-%d") if folio.check_out else "?"
            nights = 0
            if folio.check_in and folio.check_out:
                nights = max(0, (folio.check_out.date() - folio.check_in.date()).days)
            context_lines = [
                f"Guest: {partner.name}",
                f"Stay: {check_in_str} → {check_out_str}",
                f"Nights: {nights}",
                f"Adults: {folio.adults or 0}",
            ]
            if partner.country_id:
                context_lines.append(f"Country: {partner.country_id.name}")
            prompt = (
                "You are a hospitality copywriter. Personalise the following "
                "email body for this guest. Keep the structure, but warm it "
                "up, add a specific local tip, and address the guest by first "
                "name if possible. Output HTML only.\n\n"
                + "Context:\n" + "\n".join(context_lines)
                + "\n\nBody:\n" + body
            )
            result = self.env["l10n_si.ai.core"].generate(
                prompt=prompt,
                task_type=self.template_id.ai_task_type or "creative",
                max_tokens=800,
            )
            return result.get("text") if isinstance(result, dict) else False
        except Exception:  # noqa: BLE001
            return False

    # --- Cron entry --------------------------------------------------------
    @api.model
    def _cron_send_due_steps(self):
        """Called by daily cron. Sends all due scheduled steps."""
        now = fields.Datetime.now()
        due = self.search(
            [
                ("state", "=", "scheduled"),
                ("scheduled_date", "<=", now),
            ]
        )
        # Skip if guest opted out of marketing
        marketing_out = due.filtered(
            lambda s: s.partner_id and s.partner_id.message_bounce >= 5
        )
        marketing_out.action_skip("Recipient has high bounce rate")
        remaining = due - marketing_out
        remaining._send()
