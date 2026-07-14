# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HousekeepingConfig(models.Model):
    """Global configuration for the smart scheduler."""
    _name = "l10n_si.housekeeping.config"
    _description = "Housekeeping Configuration"
    _inherit = ["mail.thread"]

    name = fields.Char(required=True, default="Default")
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,
    )
    active = fields.Boolean(default=True)

    # --- Auto-generation --------------------------------------------------
    auto_create_on_checkout = fields.Boolean(
        default=True,
        help="Automatically create a turnover task when a guest checks out.",
    )
    auto_balance_cron = fields.Boolean(
        default=True,
        help="Run a daily cron to balance unassigned tasks across housekeepers.",
    )

    # --- Defaults ---------------------------------------------------------
    default_duration_minutes = fields.Integer(
        default=30,
        help="Default estimated task duration if prediction fails.",
    )
    default_priority = fields.Selection(
        [("0", "Low"), ("1", "Normal"), ("2", "High"), ("3", "Urgent")],
        default="1",
    )

    # --- Urgency thresholds (hours) --------------------------------------
    critical_threshold_hours = fields.Float(
        default=2.0,
        help="Tasks become 'critical' when the next guest arrives within this many hours.",
    )
    high_threshold_hours = fields.Float(default=4.0)
    medium_threshold_hours = fields.Float(default=8.0)

    # --- AI ---------------------------------------------------------------
    use_ai_optimization = fields.Boolean(
        default=False,
        help="Use AI Core to optimize task order (requires l10n_si_ai_core).",
    )
