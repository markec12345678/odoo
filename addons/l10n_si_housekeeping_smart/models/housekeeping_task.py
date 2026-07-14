# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models


class HousekeepingTask(models.Model):
    """Extends the base housekeeping task with smart scheduling fields."""
    _inherit = "l10n_si.housekeeping.task"

    # --- Smart scheduling -------------------------------------------------
    team_id = fields.Many2one(
        "l10n_si.housekeeping.team",
        string="Team",
        ondelete="set null",
        tracking=True,
    )
    folio_id = fields.Many2one(
        "l10n_si.hotel.folio",
        string="Outgoing Folio",
        help="The folio of the guest who checked out (for turnover tasks).",
        ondelete="set null",
    )
    next_check_in = fields.Datetime(
        compute="_compute_next_check_in",
        store=True,
        help="When the next guest is due to arrive in this room.",
    )
    urgency = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("critical", "Critical"),
        ],
        compute="_compute_urgency",
        store=True,
        help="Critical = next guest arriving in <2h. "
        "High = <4h. Medium = <8h. Low = same day or later.",
    )
    estimated_duration_minutes = fields.Integer(
        default=30,
        help="AI-predicted or rule-based estimate of how long this task takes.",
    )
    special_instructions = fields.Text(
        help="Auto-populated from pre-arrival questionnaire if applicable."
    )
    is_vip = fields.Boolean(
        default=False,
        help="Marked when the incoming or outgoing guest is a VIP.",
    )

    # --- Quality ----------------------------------------------------------
    quality_score = fields.Integer(
        help="Inspector rating 1-5 (5 = perfect).",
    )
    guest_satisfaction_score = fields.Integer(
        help="Optional: rating from post-stay questionnaire.",
    )

    # --- Mobile -----------------------------------------------------------
    mobile_pin_url = fields.Char(
        compute="_compute_mobile_pin_url",
        help="Shareable URL to pin this task on a mobile device.",
    )

    # --- Computed ---------------------------------------------------------
    @api.depends("room_id", "scheduled_date")
    def _compute_next_check_in(self):
        for task in self:
            if not task.room_id:
                task.next_check_in = False
                continue
            # Find the next reservation for this room after the task's scheduled date
            ref = task.scheduled_date or fields.Datetime.now()
            next_res = self.env["l10n_si.hotel.reservation"].search(
                [
                    ("room_id", "=", task.room_id.id),
                    ("check_in", ">=", ref),
                    ("state", "in", ["confirmed", "open"]),
                ],
                order="check_in asc",
                limit=1,
            )
            task.next_check_in = next_res.check_in if next_res else False

    @api.depends("next_check_in", "is_vip", "priority")
    def _compute_urgency(self):
        now = fields.Datetime.now()
        for task in self:
            if not task.next_check_in:
                task.urgency = "low"
                continue
            delta_hours = (task.next_check_in - now).total_seconds() / 3600
            if delta_hours < 2:
                task.urgency = "critical"
            elif delta_hours < 4:
                task.urgency = "high"
            elif delta_hours < 8:
                task.urgency = "medium"
            else:
                task.urgency = "low"

    def _compute_mobile_pin_url(self):
        base = self.env["ir.config_parameter"].get_param(
            "web.base.url", "http://localhost:8069"
        )
        for task in self:
            task.mobile_pin_url = f"{base}/housekeeping/task/{task.id}"

    # --- Smart scheduling methods ----------------------------------------
    @api.model
    def _predict_duration(self, room, folio):
        """Predict turnover time in minutes based on room type and stay data.

        Returns minutes. Default 30 if no data.
        """
        if not room:
            return 30
        base = 30  # standard room
        room_type_name = (room.room_type_id.name or "").lower()
        # Suites take longer
        if "suite" in room_type_name:
            base = 50
        elif "deluxe" in room_type_name:
            base = 40
        elif "family" in room_type_name:
            base = 45
        # Longer stays → more cleaning
        if folio and folio.check_in and folio.check_out:
            nights = (folio.check_out.date() - folio.check_in.date()).days
            if nights > 7:
                base += 15
            elif nights > 3:
                base += 5
        # More guests → more cleaning
        if folio:
            if folio.adults and folio.adults > 2:
                base += (folio.adults - 2) * 5
            if folio.children:
                base += folio.children * 5
        # Pets (if module installed and pet was present)
        pet_module = self.env["ir.module.module"].search(
            [("name", "=", "l10n_si_pets"), ("state", "=", "installed")],
            limit=1,
        )
        if pet_module and folio and folio.partner_id:
            # Check if guest had a pet — for now, simple heuristic
            pass
        return base

    @api.model
    def _auto_create_turnover_task(self, folio):
        """Called when a guest checks out — creates a turnover cleaning task.

        Args:
            folio: the l10n_si.hotel.folio of the guest who just checked out.
        """
        if not folio or not folio.room_ids:
            return False
        existing = self.search(
            [
                ("folio_id", "=", folio.id),
                ("task_type", "=", "checkout"),
            ],
            limit=1,
        )
        if existing:
            return existing.id
        # Find the main room (first one)
        room = folio.room_ids[0]
        # Predict duration
        duration = self._predict_duration(room, folio)
        # Find the right team for this floor
        team = self._find_team_for_floor(room.floor or 1)
        # Check for special instructions from questionnaire
        instructions = self._get_special_instructions(folio)
        # Determine VIP status
        is_vip = folio.partner_id and bool(
            folio.partner_id.category_id.filtered(
                lambda c: "vip" in (c.name or "").lower()
            )
        )
        task_vals = {
            "room_id": room.id,
            "folio_id": folio.id,
            "task_type": "checkout",
            "scheduled_date": fields.Datetime.now(),
            "priority": "2" if is_vip else "1",
            "state": "assigned" if team else "pending",
            "team_id": team.id if team else False,
            "housekeeper_id": team.leader_id.id if team and team.leader_id else False,
            "estimated_duration_minutes": duration,
            "special_instructions": instructions,
            "is_vip": is_vip,
        }
        task = self.create(task_vals)
        # Post a message to the folio
        folio.message_post(
            body=_("Housekeeping task <b>%s</b> created. Estimated duration: %d min.") % (task.name, duration),
            subject=_("Turnover task scheduled"),
        )
        return task.id

    @api.model
    def _find_team_for_floor(self, floor):
        """Find the team that handles the given floor."""
        return self.env["l10n_si.housekeeping.team"].search(
            [
                ("active", "=", True),
                ("floor_from", "<=", floor),
                ("floor_to", ">=", floor),
                "|",
                ("company_id", "=", self.env.company.id),
                ("company_id", "=", False),
            ],
            order="company_id desc",
            limit=1,
        )

    @api.model
    def _get_special_instructions(self, folio):
        """Get special instructions from pre-arrival questionnaire if installed."""
        questionnaire_module = self.env["ir.module.module"].search(
            [
                ("name", "=", "l10n_si_pre_arrival_questionnaire"),
                ("state", "=", "installed"),
            ],
            limit=1,
        )
        if not questionnaire_module or not folio.partner_id:
            return ""
        # Look for questionnaire responses linked to this folio
        responses = self.env["l10n_si.questionnaire.response"].search(
            [
                ("folio_id", "=", folio.id),
                ("state", "=", "completed"),
            ],
            limit=1,
        )
        if not responses:
            return ""
        resp = responses[0]
        lines = []
        if resp.allergies:
            lines.append(f"⚠️ ALLERGIES: {resp.allergies}")
        if resp.notes:
            lines.append(f"Guest notes: {resp.notes}")
        if resp.special_occasion and resp.special_occasion != "none":
            lines.append(f"Special occasion: {resp.special_occasion}")
        return "\n".join(lines)

    # --- Workload balancing ----------------------------------------------
    @api.model
    def _balance_workload(self, date=None):
        """Redistribute today's unassigned tasks across housekeepers based
        on current workload and team zones.

        Called by daily cron at shift start.
        """
        if date is None:
            date = fields.Date.today()
        date_start = fields.Datetime.to_string(date) + " 00:00:00"
        date_end = fields.Datetime.to_string(date) + " 23:59:59"
        unassigned = self.search(
            [
                ("scheduled_date", ">=", date_start),
                ("scheduled_date", "<=", date_end),
                ("state", "=", "pending"),
            ]
        )
        for task in unassigned:
            team = self._find_team_for_floor(task.room_id.floor or 1)
            if not team:
                continue
            # Find the team member with the least tasks today
            member = self._find_least_loaded_member(team, date)
            task.write(
                {
                    "team_id": team.id,
                    "housekeeper_id": member.id if member else (team.leader_id.id if team.leader_id else False),
                    "state": "assigned",
                }
            )
        return True

    @api.model
    def _find_least_loaded_member(self, team, date):
        """Find team member with fewest assigned tasks today."""
        if not team.member_ids:
            return False
        date_start = fields.Datetime.to_string(date) + " 00:00:00"
        date_end = fields.Datetime.to_string(date) + " 23:59:59"
        counts = {}
        for member in team.member_ids:
            count = self.search_count(
                [
                    ("housekeeper_id", "=", member.id),
                    ("scheduled_date", ">=", date_start),
                    ("scheduled_date", "<=", date_end),
                    ("state", "in", ["assigned", "in_progress"]),
                ]
            )
            counts[member.id] = count
        # Find the member with the minimum count
        if not counts:
            return False
        min_id = min(counts, key=counts.get)
        return team.member_ids.filtered(lambda m: m.id == min_id)

    # --- AI optimization (optional) --------------------------------------
    def action_optimize_with_ai(self):
        """Use AI Core to optimize the order of tasks for the team.

        Requires l10n_si_ai_core to be installed.
        """
        ai_module = self.env["ir.module.module"].search(
            [("name", "=", "l10n_si_ai_core"), ("state", "=", "installed")],
            limit=1,
        )
        if not ai_module:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("AI Core not installed"),
                    "message": _("Install l10n_si_ai_core to use AI optimization."),
                    "type": "warning",
                },
            }
        # Group tasks by team and optimize each
        for team in self.mapped("team_id"):
            team_tasks = self.filtered(lambda t: t.team_id == team and t.state in ("pending", "assigned"))
            if len(team_tasks) < 2:
                continue
            prompt = self._build_optimization_prompt(team_tasks)
            try:
                result = self.env["l10n_si.ai.core"].generate(
                    prompt=prompt,
                    task_type="reasoning",
                    max_tokens=500,
                )
                optimization = result.get("text", "") if isinstance(result, dict) else ""
                # Apply suggested ordering (simple: parse room numbers from response)
                self._apply_ai_ordering(team_tasks, optimization)
            except Exception:  # noqa: BLE001
                continue
        return True

    def _build_optimization_prompt(self, tasks):
        """Build a prompt for the AI to optimize task order."""
        lines = [
            "You are a hotel housekeeping scheduler. Optimize the order of these",
            "cleaning tasks to minimize walking distance and respect priorities.",
            "Output a comma-separated list of room numbers in optimal order.",
            "",
            "Tasks:",
        ]
        for i, t in enumerate(tasks, 1):
            room = t.room_id
            lines.append(
                f"{i}. Room {room.number} (floor {room.floor}, "
                f"urgency={t.urgency}, est={t.estimated_duration_minutes}min)"
            )
        return "\n".join(lines)

    def _apply_ai_ordering(self, tasks, ai_response):
        """Apply the ordering suggested by AI by updating scheduled_date."""
        import re
        # Extract room numbers from the AI response
        room_numbers = re.findall(r"\d+", ai_response)
        if not room_numbers:
            return
        # Re-sequence: tasks mentioned first get earlier scheduled_date
        base_time = fields.Datetime.now()
        from datetime import timedelta

        for idx, room_num in enumerate(room_numbers):
            task = tasks.filtered(lambda t: t.room_id.number == room_num)
            if task:
                task.write({"scheduled_date": base_time + timedelta(minutes=idx * 5)})

    # --- Cron -------------------------------------------------------------
    @api.model
    def _cron_balance_workload(self):
        """Daily cron — balance today's unassigned tasks."""
        self._balance_workload()

    @api.model
    def _cron_update_urgency(self):
        """Hourly cron — recompute urgency based on next check-in time."""
        tasks = self.search(
            [("state", "in", ["pending", "assigned", "in_progress"])]
        )
        for task in tasks:
            task._compute_urgency()
