# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import secrets
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class KioskSession(models.Model):
    """Tracks a single kiosk check-in interaction.

    A session is created when a guest starts a check-in at the kiosk and
    progresses through stages until completion (or abandonment).
    """
    _name = "l10n_si.kiosk.session"
    _description = "Kiosk Check-in Session"
    _inherit = ["mail.thread"]
    _order = "create_date desc"

    name = fields.Char(compute="_compute_name", store=True)
    token = fields.Char(
        required=True,
        copy=False,
        default=lambda self: self._generate_token(),
        index=True,
        help="Random token used to authenticate the kiosk session without login.",
    )
    config_id = fields.Many2one(
        "l10n_si.kiosk.config",
        required=True,
        ondelete="restrict",
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
        related="config_id.company_id",
        store=True,
    )

    # --- State machine ----------------------------------------------------
    state = fields.Selection(
        [
            ("welcome", "Welcome"),
            ("lookup", "Booking lookup"),
            ("confirm", "Confirm booking"),
            ("scan", "Document scan"),
            ("review", "Review data"),
            ("signature", "Signature"),
            ("done", "Completed"),
            ("abandoned", "Abandoned"),
            ("failed", "Failed"),
        ],
        default="welcome",
        required=True,
        tracking=True,
    )
    previous_state = fields.Char()

    # --- Captured data ----------------------------------------------------
    booking_ref = fields.Char(string="Booking Reference Entered")
    document_scan_id = fields.Many2one(
        "l10n_si.document.scan",
        string="Document Scan",
        ondelete="set null",
    )
    guest_first_name = fields.Char()
    guest_last_name = fields.Char()
    guest_nationality = fields.Char()
    guest_doc_type = fields.Selection(
        [
            ("passport", "Passport"),
            ("id_card", "ID Card"),
            ("drivers_license", "Driver's License"),
        ],
    )
    guest_doc_number = fields.Char()
    guest_birth_date = fields.Date()
    guest_gender = fields.Selection(
        [("male", "Male"), ("female", "Female"), ("other", "Other")]
    )
    guest_address = fields.Char()
    guest_city = fields.Char()
    guest_country_id = fields.Many2one("res.country")
    guest_email = fields.Char()
    guest_phone = fields.Char()
    signature = fields.Binary(string="Signature Image")
    arrival_time = fields.Char(string="Actual arrival time")
    adults_count = fields.Integer(default=1)
    children_count = fields.Integer(default=0)

    # --- Outcome ----------------------------------------------------------
    etourism_registration_id = fields.Many2one(
        "l10n_si.etourism.guest.registration",
        string="eTurizem Registration Created",
        ondelete="set null",
        readonly=True,
    )
    room_number = fields.Char(readonly=True)
    key_card_code = fields.Char(readonly=True)
    wifi_network = fields.Char(readonly=True)
    wifi_password = fields.Char(readonly=True)
    error_message = fields.Text(readonly=True)
    duration_seconds = fields.Integer(compute="_compute_duration", store=True)

    # --- Activity log -----------------------------------------------------
    last_activity = fields.Datetime(default=fields.Datetime.now)
    complete_date = fields.Datetime(readonly=True)

    # --- Constraints ------------------------------------------------------
    _sql_constraints = [
        (
            "token_unique",
            "UNIQUE(token)",
            "Kiosk session token must be unique.",
        ),
    ]

    @api.model
    def _generate_token(self):
        return secrets.token_urlsafe(24)

    @api.depends("folio_id.name", "create_date", "state")
    def _compute_name(self):
        for s in self:
            folio = s.folio_id.name or "—"
            date = fields.Datetime.to_string(s.create_date)[:16] if s.create_date else ""
            s.name = f"Kiosk {folio} ({date})"

    @api.depends("create_date", "complete_date")
    def _compute_duration(self):
        for s in self:
            if not s.create_date:
                s.duration_seconds = 0
                continue
            end = s.complete_date or fields.Datetime.now()
            delta = end - s.create_date
            s.duration_seconds = int(delta.total_seconds())

    # --- State transitions ------------------------------------------------
    def _transition(self, new_state, **vals):
        """Move session to a new state, recording previous and updating vals."""
        self.ensure_one()
        vals["previous_state"] = self.state
        vals["state"] = new_state
        vals["last_activity"] = fields.Datetime.now()
        return self.write(vals)

    def action_start(self):
        """Guest tapped 'Start check-in' — move to lookup state."""
        self.ensure_one()
        self._transition("lookup")

    def action_lookup_booking(self, booking_ref):
        """Look up a folio by name, partner email, or booking reference."""
        self.ensure_one()
        folio = self._find_folio(booking_ref)
        if not folio:
            return False
        self.write(
            {
                "folio_id": folio.id,
                "partner_id": folio.partner_id.id,
                "booking_ref": booking_ref,
                "adults_count": folio.adults or 1,
                "children_count": folio.children or 0,
            }
        )
        self._transition("confirm")
        return folio

    def _find_folio(self, ref):
        """Find a folio by reference number, partner name, or partner email."""
        if not ref:
            return self.env["l10n_si.hotel.folio"]
        ref = ref.strip()
        domain = [
            ("company_id", "=", self.company_id.id),
            ("state", "in", ["draft", "open", "confirmed"]),
        ]
        # Try folio name first (e.g. FOL/2026/0001)
        folio = self.env["l10n_si.hotel.folio"].search(
            domain + [("name", "ilike", ref)], limit=1
        )
        if folio:
            return folio
        # Try partner email
        partner = self.env["res.partner"].search(
            [("email", "ilike", ref)], limit=1
        )
        if partner:
            folio = self.env["l10n_si.hotel.folio"].search(
                domain + [("partner_id", "=", partner.id)], limit=1
            )
            if folio:
                return folio
        # Try partner name
        partner = self.env["res.partner"].search(
            [("name", "ilike", ref)], limit=1
        )
        if partner:
            folio = self.env["l10n_si.hotel.folio"].search(
                domain + [("partner_id", "=", partner.id)], limit=1
            )
            if folio:
                return folio
        return self.env["l10n_si.hotel.folio"]

    def action_confirm_booking(self):
        """Guest confirmed the booking — proceed to scan."""
        self.ensure_one()
        if not self.folio_id:
            raise UserError(_("No folio associated with this session."))
        self._transition("scan")

    def action_back_to_lookup(self):
        self.ensure_one()
        self._transition("lookup")

    def action_save_scan_data(self, scan_data):
        """Save data extracted from document scan and move to review."""
        self.ensure_one()
        vals = {}
        if scan_data.get("first_name"):
            vals["guest_first_name"] = scan_data["first_name"]
        if scan_data.get("last_name"):
            vals["guest_last_name"] = scan_data["last_name"]
        if scan_data.get("nationality"):
            country = self.env["res.country"].search(
                [
                    "|",
                    ("code", "=", scan_data["nationality"][:2].upper()),
                    ("name", "ilike", scan_data["nationality"]),
                ],
                limit=1,
            )
            if country:
                vals["guest_country_id"] = country.id
                vals["guest_nationality"] = country.name
            else:
                vals["guest_nationality"] = scan_data["nationality"]
        if scan_data.get("doc_number"):
            vals["guest_doc_number"] = scan_data["doc_number"]
        if scan_data.get("doc_type"):
            vals["guest_doc_type"] = scan_data["doc_type"]
        if scan_data.get("birth_date"):
            vals["guest_birth_date"] = scan_data["birth_date"]
        if scan_data.get("gender"):
            vals["guest_gender"] = scan_data["gender"]
        if scan_data.get("scan_id"):
            vals["document_scan_id"] = scan_data["scan_id"]
        self._transition("review", **vals)

    def action_skip_scan(self):
        """Guest chose to enter data manually — pre-fill from partner."""
        self.ensure_one()
        partner = self.partner_id
        vals = {}
        if partner.name:
            parts = partner.name.split(" ", 1)
            vals["guest_first_name"] = parts[0]
            vals["guest_last_name"] = parts[1] if len(parts) > 1 else ""
        if partner.country_id:
            vals["guest_country_id"] = partner.country_id.id
            vals["guest_nationality"] = partner.country_id.name
        if partner.email:
            vals["guest_email"] = partner.email
        if partner.mobile or partner.phone:
            vals["guest_phone"] = partner.mobile or partner.phone
        if partner.city:
            vals["guest_city"] = partner.city
        if partner.street:
            vals["guest_address"] = partner.street
        self._transition("review", **vals)

    def action_save_review(self, review_data):
        """Guest confirmed the reviewed data — proceed to signature."""
        self.ensure_one()
        allowed = [
            "guest_first_name", "guest_last_name", "guest_nationality",
            "guest_doc_type", "guest_doc_number", "guest_birth_date",
            "guest_gender", "guest_address", "guest_city",
            "guest_email", "guest_phone", "guest_country_id",
            "arrival_time", "adults_count", "children_count",
        ]
        vals = {k: v for k, v in review_data.items() if k in allowed}
        self._transition("signature", **vals)

    def action_back_to_review(self):
        self.ensure_one()
        self._transition("review")

    def action_save_signature(self, signature_base64):
        """Guest signed — complete the check-in."""
        self.ensure_one()
        self.write({"signature": signature_base64})
        return self.action_complete()

    def action_complete(self):
        """Finalize the check-in: update partner, create eTurizem reg,
        assign room, send notification to reception.
        """
        self.ensure_one()
        try:
            # 1. Update partner record with captured data
            self._update_partner()

            # 2. Update folio with arrival time and guest count
            self._update_folio()

            # 3. Create eTurizem guest registration if module is installed
            reg = self._create_etourism_registration()

            # 4. Assign room from existing reservation
            room_number = self._get_room_number()

            # 5. Generate key card code
            key_card = self._generate_key_card()

            # 6. Get Wi-Fi credentials from config
            wifi_net = self.config_id.wifi_network or "HotelGuest"
            wifi_pass = self.config_id.wifi_password or "welcome2024"

            self.write(
                {
                    "etourism_registration_id": reg.id if reg else False,
                    "room_number": room_number,
                    "key_card_code": key_card,
                    "wifi_network": wifi_net,
                    "wifi_password": wifi_pass,
                    "complete_date": fields.Datetime.now(),
                }
            )
            self._transition("done")
            self._notify_reception()
            return True
        except Exception as e:  # noqa: BLE001
            self.write({"error_message": str(e)[:500]})
            self._transition("failed")
            return False

    def action_abandon(self):
        """Guest walked away / timed out — mark as abandoned."""
        for s in self:
            if s.state in ("done", "failed"):
                continue
            s._transition("abandoned")

    def action_retry(self):
        self.ensure_one()
        if self.state != "failed":
            return False
        # Restart from scan
        self._transition("scan", error_message=False)
        return True

    # --- Helper methods ---------------------------------------------------
    def _update_partner(self):
        """Update the partner record with captured guest data."""
        self.ensure_one()
        if not self.partner_id:
            return
        partner_vals = {}
        if self.guest_email and not self.partner_id.email:
            partner_vals["email"] = self.guest_email
        if self.guest_phone and not self.partner_id.mobile:
            partner_vals["mobile"] = self.guest_phone
        if self.guest_country_id and not self.partner_id.country_id:
            partner_vals["country_id"] = self.guest_country_id.id
        if self.guest_city and not self.partner_id.city:
            partner_vals["city"] = self.guest_city
        if self.guest_address and not self.partner_id.street:
            partner_vals["street"] = self.guest_address
        if partner_vals:
            self.partner_id.write(partner_vals)

    def _update_folio(self):
        """Update the folio with actual arrival info."""
        self.ensure_one()
        if not self.folio_id:
            return
        folio_vals = {}
        if self.adults_count:
            folio_vals["adults"] = self.adults_count
        if self.children_count is not False:
            folio_vals["children"] = self.children_count
        if folio_vals:
            self.folio_id.write(folio_vals)

    def _create_etourism_registration(self):
        """Create an AJPES eTurizem guest registration record if the
        etourism module is installed.
        """
        self.ensure_one()
        etourism_installed = self.env["ir.module.module"].search(
            [("name", "=", "l10n_si_etourism"), ("state", "=", "installed")],
            limit=1,
        )
        if not etourism_installed:
            return self.env["l10n_si.etourism.guest.registration"]
        if not self.guest_first_name or not self.guest_last_name:
            return self.env["l10n_si.etourism.guest.registration"]
        # Find the establishment for this company
        establishment = self.env["l10n_si.etourism.establishment"].search(
            [("company_id", "=", self.company_id.id)], limit=1
        )
        if not establishment:
            return self.env["l10n_si.etourism.guest.registration"]
        vals = {
            "establishment_id": establishment.id,
            "guest_first_name": self.guest_first_name,
            "guest_last_name": self.guest_last_name,
            "guest_country_id": self.guest_country_id.id if self.guest_country_id else False,
            "guest_doc_type": self.guest_doc_type or "passport",
            "guest_doc_number": self.guest_doc_number or "",
            "guest_birth_date": self.guest_birth_date or False,
            "partner_id": self.partner_id.id if self.partner_id else False,
            "folio_id": self.folio_id.id if self.folio_id else False,
            "arrival_date": fields.Datetime.now(),
            "state": "draft",
        }
        try:
            return self.env["l10n_si.etourism.guest.registration"].create(vals)
        except Exception:  # noqa: BLE001
            return self.env["l10n_si.etourism.guest.registration"]

    def _get_room_number(self):
        """Get the room number from the folio's reservation."""
        self.ensure_one()
        if not self.folio_id:
            return ""
        reservation = self.env["l10n_si.hotel.reservation"].search(
            [("folio_id", "=", self.folio_id.id)], limit=1
        )
        if reservation and reservation.room_id:
            return reservation.room_id.name or reservation.room_id.number or ""
        return ""

    def _generate_key_card_code(self):
        """Generate a random key card code."""
        self.ensure_one()
        import random
        import string
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

    def _notify_reception(self):
        """Post a message in the folio chatter to alert reception."""
        self.ensure_one()
        if not self.folio_id:
            return
        body = _(
            "Kiosk self check-in completed by %(name)s. "
            "Room: %(room)s, Key card: %(key)s, "
            "eTurizem registration: %(reg)s"
        ) % {
            "name": f"{self.guest_first_name or ''} {self.guest_last_name or ''}".strip(),
            "room": self.room_number or "—",
            "key": self.key_card_code or "—",
            "reg": self.etourism_registration_id.name or "—",
        }
        self.folio_id.message_post(body=body, subject=_("Kiosk check-in completed"))

    # --- Cron -------------------------------------------------------------
    @api.model
    def _cron_abandon_stale_sessions(self):
        """Mark sessions with no activity for >30 minutes as abandoned."""
        cutoff = fields.Datetime.now() - timedelta(minutes=30)
        stale = self.search(
            [
                ("last_activity", "<", cutoff),
                ("state", "in", ["welcome", "lookup", "confirm", "scan",
                                 "review", "signature"]),
            ]
        )
        stale.action_abandon()
