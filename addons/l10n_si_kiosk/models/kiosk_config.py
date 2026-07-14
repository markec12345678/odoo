# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class KioskConfig(models.Model):
    """Configuration for a physical kiosk device.

    Each kiosk device in the hotel has its own config record that specifies:
      * Welcome screen text (multilingual)
      * Wi-Fi credentials shown to guests on completion
      * Logo and brand colors
      * Idle timeout
      * Whether to require document scan or allow manual entry
      * Whether to auto-submit eTurizem registration
    """
    _name = "l10n_si.kiosk.config"
    _description = "Kiosk Configuration"
    _inherit = ["mail.thread"]
    _order = "name"

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,
    )
    location = fields.Char(
        help="Physical location of the kiosk, e.g. 'Main lobby', 'Spa entrance'.",
    )

    # --- Branding ---------------------------------------------------------
    logo = fields.Binary(related="company_id.logo", store=False)
    primary_color = fields.Char(
        default="#875A7B",
        help="Primary brand color (hex).",
    )
    welcome_text = fields.Text(
        default="Welcome! Tap below to check in.",
        translate=True,
    )
    welcome_text_hr = fields.Text(
        default="Dobrodošli! Kliknite spodaj za prijavo.",
        string="Welcome Text (HR)",
    )
    welcome_text_sl = fields.Text(
        default="Dobrodošli! Kliknite spodaj za prijavo.",
        string="Welcome Text (SL)",
    )

    # --- Behavior ---------------------------------------------------------
    idle_timeout_seconds = fields.Integer(
        default=60,
        help="Seconds of inactivity before returning to welcome screen.",
    )
    require_document_scan = fields.Boolean(
        default=False,
        help="If set, guests must scan a document. If not, manual entry is allowed.",
    )
    auto_submit_etourism = fields.Boolean(
        default=True,
        help="Automatically submit eTurizem registration after check-in.",
    )
    allow_skip_scan = fields.Boolean(
        default=True,
        help="Allow guest to skip document scan and enter data manually.",
    )

    # --- Wi-Fi credentials (shown on completion screen) -------------------
    wifi_network = fields.Char(default="HotelGuest")
    wifi_password = fields.Char(default="welcome2024")

    # --- Reception notification -------------------------------------------
    notify_user_ids = fields.Many2many(
        "res.users",
        string="Notify on Completion",
        help="Users who will be notified when a guest completes check-in.",
    )

    # --- Stats ------------------------------------------------------------
    session_ids = fields.One2many(
        "l10n_si.kiosk.session", "config_id", string="Sessions"
    )
    session_count = fields.Integer(compute="_compute_session_count")
    completed_count = fields.Integer(compute="_compute_session_count")
    abandoned_count = fields.Integer(compute="_compute_session_count")

    def _compute_session_count(self):
        for cfg in self:
            sessions = cfg.session_ids
            cfg.session_count = len(sessions)
            cfg.completed_count = len(sessions.filtered(lambda s: s.state == "done"))
            cfg.abandoned_count = len(sessions.filtered(lambda s: s.state == "abandoned"))

    def action_open_kiosk(self):
        """Open the kiosk URL in a new tab."""
        self.ensure_one()
        base = self.env["ir.config_parameter"].get_param(
            "web.base.url", "http://localhost:8069"
        )
        return {
            "type": "ir.actions.act_url",
            "url": f"{base}/kiosk/start?config_id={self.id}",
            "target": "new",
        }
