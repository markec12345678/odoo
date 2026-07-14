# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HotelFolio(models.Model):
    _inherit = "l10n_si.hotel.folio"

    journey_step_ids = fields.One2many(
        "l10n_si.guest.journey.step",
        "folio_id",
        string="Guest Journey",
    )
    journey_step_count = fields.Integer(
        compute="_compute_journey_step_count"
    )
    journey_state = fields.Selection(
        [
            ("not_started", "Not started"),
            ("pre_arrival", "Pre-arrival"),
            ("in_stay", "In-stay"),
            ("post_stay", "Post-stay"),
            ("completed", "Completed"),
        ],
        compute="_compute_journey_state",
        store=True,
    )
    journey_progress = fields.Float(
        compute="_compute_journey_progress",
        help="Percentage of journey steps that have been sent.",
    )

    @api.depends("journey_step_ids.state")
    def _compute_journey_step_count(self):
        for folio in self:
            folio.journey_step_count = len(folio.journey_step_ids)

    @api.depends(
        "journey_step_ids.state",
        "check_in",
        "check_out",
        "state",
    )
    def _compute_journey_state(self):
        today = fields.Date.today()
        for folio in self:
            if not folio.journey_step_ids:
                folio.journey_state = "not_started"
            elif folio.state in ("draft", "cancelled"):
                folio.journey_state = "not_started"
            elif folio.check_out and folio.check_out.date() < today:
                folio.journey_state = "post_stay"
            elif folio.check_in and folio.check_in.date() <= today:
                folio.journey_state = "in_stay"
            elif folio.check_in and folio.check_in.date() > today:
                folio.journey_state = "pre_arrival"
            else:
                folio.journey_state = "not_started"

    @api.depends("journey_step_ids.state")
    def _compute_journey_progress(self):
        for folio in self:
            steps = folio.journey_step_ids
            if not steps:
                folio.journey_progress = 0.0
                continue
            done = len(steps.filtered(lambda s: s.state == "sent"))
            folio.journey_progress = (done / len(steps)) * 100.0

    # --- Actions -----------------------------------------------------------
    def action_generate_journey(self):
        """Generate journey steps for this folio based on active templates."""
        self.ensure_one()
        if not self.partner_id:
            return {"type": "ir.actions.act_window_close"}
        templates = self.env["l10n_si.guest.journey.template"].search(
            [
                ("active", "=", True),
                ("company_id", "in", [self.company_id.id, False]),
            ]
        )
        # Filter by language if partner has one
        if self.partner_id.lang:
            lang = self.env["res.lang"].search(
                [("code", "=", self.partner_id.lang)], limit=1
            )
            if lang:
                # Prefer language-specific templates; fall back to generic
                specific = templates.filtered(lambda t: t.lang_id == lang)
                generic = templates.filtered(lambda t: not t.lang_id)
                # For each (stage, offset) tuple, prefer specific over generic
                seen = set()
                ordered = self.env["l10n_si.guest.journey.template"]
                for tmpl in list(specific) + list(generic):
                    key = (tmpl.stage, tmpl.trigger_event, tmpl.offset_days)
                    if key in seen:
                        continue
                    seen.add(key)
                    ordered |= tmpl
                templates = ordered

        new_steps = self.env["l10n_si.guest.journey.step"]
        for tmpl in templates:
            sched = tmpl._compute_scheduled_date(self)
            if not sched:
                continue
            # Skip if a step for this template already exists on the folio
            existing = self.env["l10n_si.guest.journey.step"].search(
                [
                    ("folio_id", "=", self.id),
                    ("template_id", "=", tmpl.id),
                    ("state", "!=", "skipped"),
                ],
                limit=1,
            )
            if existing:
                continue
            new_steps |= self.env["l10n_si.guest.journey.step"].create(
                {
                    "folio_id": self.id,
                    "template_id": tmpl.id,
                    "scheduled_date": sched,
                    "state": "scheduled",
                }
            )
        return {
            "type": "ir.actions.act_window",
            "name": "Guest Journey",
            "res_model": "l10n_si.guest.journey.step",
            "view_mode": "kanban,tree,form",
            "domain": [("folio_id", "=", self.id)],
            "context": {"default_folio_id": self.id},
            "target": "current",
        }

    def action_view_journey(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Guest Journey",
            "res_model": "l10n_si.guest.journey.step",
            "view_mode": "kanban,tree,form",
            "domain": [("folio_id", "=", self.id)],
            "context": {"default_folio_id": self.id},
            "target": "current",
        }
