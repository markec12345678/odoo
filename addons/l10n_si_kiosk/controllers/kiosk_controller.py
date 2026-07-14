# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import json
import logging

from odoo import _, http
from odoo.http import request

_logger = logging.getLogger(__name__)


class KioskController(http.Controller):
    """Public kiosk controller — no login required (token-authenticated sessions).

    All routes are accessible without authentication because the kiosk is a
    shared device in a public lobby. Session tokens prevent CSRF.
    """

    # ----- Helpers --------------------------------------------------------
    def _get_config(self, config_id=None):
        """Get the kiosk config — by ID, or the first active one."""
        domain = [("active", "=", True)]
        if config_id:
            domain.append(("id", "=", int(config_id)))
        return request.env["l10n_si.kiosk.config"].search(domain, limit=1)

    def _get_session(self, token):
        if not token:
            return request.env["l10n_si.kiosk.session"]
        return request.env["l10n_si.kiosk.session"].search(
            [("token", "=", token)], limit=1
        )

    def _get_lang(self):
        """Detect language from cookie or partner."""
        lang = request.httprequest.cookies.get("kiosk_lang")
        if lang in ["en_US", "sl_SI", "hr_HR", "de_DE", "it_IT"]:
            return lang
        return "en_US"

    def _render(self, template, values=None):
        """Render a kiosk template with common values."""
        if values is None:
            values = {}
        values.setdefault("lang", self._get_lang())
        return request.render(template, values)

    # ----- Routes ---------------------------------------------------------
    @http.route("/kiosk/start", type="http", auth="public", website=True)
    def kiosk_start(self, config_id=None, **kw):
        """Welcome screen — guest taps 'Start' to begin."""
        config = self._get_config(config_id)
        if not config:
            return request.not_found(_("No active kiosk configuration found."))
        session = request.env["l10n_si.kiosk.session"].create(
            {"config_id": config.id}
        )
        return self._render(
            "l10n_si_kiosk.welcome",
            {
                "config": config,
                "session": session,
                "token": session.token,
            },
        )

    @http.route("/kiosk/lookup", type="http", auth="public", website=True, methods=["POST"])
    def kiosk_lookup(self, token, booking_ref, **kw):
        """Guest entered a booking reference — look up folio."""
        session = self._get_session(token)
        if not session:
            return request.not_found(_("Invalid session."))
        folio = session.action_lookup_booking(booking_ref)
        if not folio:
            return self._render(
                "l10n_si_kiosk.lookup",
                {
                    "config": session.config_id,
                    "session": session,
                    "token": token,
                    "error": _("Booking not found. Please check your reference."),
                    "booking_ref": booking_ref,
                },
            )
        return self._render(
            "l10n_si_kiosk.confirm",
            {
                "config": session.config_id,
                "session": session,
                "token": token,
                "folio": folio,
            },
        )

    @http.route("/kiosk/lookup_screen", type="http", auth="public", website=True)
    def kiosk_lookup_screen(self, token, **kw):
        """Show the lookup screen (after Start tapped or back from confirm)."""
        session = self._get_session(token)
        if not session:
            return request.not_found(_("Invalid session."))
        session.action_start()
        return self._render(
            "l10n_si_kiosk.lookup",
            {
                "config": session.config_id,
                "session": session,
                "token": token,
                "error": None,
            },
        )

    @http.route("/kiosk/confirm", type="http", auth="public", website=True, methods=["POST"])
    def kiosk_confirm(self, token, **kw):
        """Guest confirmed the booking — proceed to scan."""
        session = self._get_session(token)
        if not session:
            return request.not_found(_("Invalid session."))
        session.action_confirm_booking()
        return self._render(
            "l10n_si_kiosk.scan",
            {
                "config": session.config_id,
                "session": session,
                "token": token,
            },
        )

    @http.route("/kiosk/back_to_lookup", type="http", auth="public", website=True, methods=["POST"])
    def kiosk_back_to_lookup(self, token, **kw):
        session = self._get_session(token)
        if not session:
            return request.not_found(_("Invalid session."))
        session.action_back_to_lookup()
        return self._render(
            "l10n_si_kiosk.lookup",
            {
                "config": session.config_id,
                "session": session,
                "token": token,
                "error": None,
            },
        )

    @http.route("/kiosk/skip_scan", type="http", auth="public", website=True, methods=["POST"])
    def kiosk_skip_scan(self, token, **kw):
        """Guest chose to enter data manually."""
        session = self._get_session(token)
        if not session:
            return request.not_found(_("Invalid session."))
        session.action_skip_scan()
        return self._render(
            "l10n_si_kiosk.review",
            {
                "config": session.config_id,
                "session": session,
                "token": token,
                "countries": request.env["res.country"].search([]),
            },
        )

    @http.route("/kiosk/upload_scan", type="http", auth="public", website=True, methods=["POST"])
    def kiosk_upload_scan(self, token, **kw):
        """Guest uploaded a passport/ID scan image."""
        session = self._get_session(token)
        if not session:
            return request.not_found(_("Invalid session."))
        upload = kw.get("scan_file")
        if not upload or not upload.filename:
            return self._render(
                "l10n_si_kiosk.scan",
                {
                    "config": session.config_id,
                    "session": session,
                    "token": token,
                    "error": _("No file uploaded. Please try again."),
                },
            )
        # Try to use l10n_si_document_scan if installed
        scan_module = request.env["ir.module.module"].search(
            [("name", "=", "l10n_si_document_scan"), ("state", "=", "installed")],
            limit=1,
        )
        scan_data = {}
        if scan_module:
            try:
                scan = request.env["l10n_si.document.scan"].create(
                    {
                        "document_image": base64.b64encode(upload.read()).decode(),
                        "document_type": "passport",
                    }
                )
                scan.action_run_ocr()
                scan_data = {
                    "scan_id": scan.id,
                    "first_name": scan.first_name,
                    "last_name": scan.last_name,
                    "nationality": scan.nationality,
                    "doc_number": scan.document_number,
                    "doc_type": scan.document_type,
                    "birth_date": scan.birth_date,
                    "gender": scan.gender,
                }
            except Exception as e:  # noqa: BLE001
                _logger.warning("Kiosk OCR failed: %s", e)
        session.action_save_scan_data(scan_data)
        return self._render(
            "l10n_si_kiosk.review",
            {
                "config": session.config_id,
                "session": session,
                "token": token,
                "countries": request.env["res.country"].search([]),
            },
        )

    @http.route("/kiosk/save_review", type="http", auth="public", website=True, methods=["POST"])
    def kiosk_save_review(self, token, **kw):
        """Guest reviewed/edited data — proceed to signature."""
        session = self._get_session(token)
        if not session:
            return request.not_found(_("Invalid session."))
        review_data = self._extract_review_data(kw)
        session.action_save_review(review_data)
        return self._render(
            "l10n_si_kiosk.signature",
            {
                "config": session.config_id,
                "session": session,
                "token": token,
            },
        )

    @http.route("/kiosk/back_to_review", type="http", auth="public", website=True, methods=["POST"])
    def kiosk_back_to_review(self, token, **kw):
        session = self._get_session(token)
        if not session:
            return request.not_found(_("Invalid session."))
        session.action_back_to_review()
        return self._render(
            "l10n_si_kiosk.review",
            {
                "config": session.config_id,
                "session": session,
                "token": token,
                "countries": request.env["res.country"].search([]),
            },
        )

    @http.route("/kiosk/complete", type="http", auth="public", website=True, methods=["POST"])
    def kiosk_complete(self, token, signature, **kw):
        """Guest signed — finalize the check-in."""
        session = self._get_session(token)
        if not session:
            return request.not_found(_("Invalid session."))
        # signature is a base64 PNG data URL — strip prefix
        sig_data = signature
        if sig_data and "," in sig_data:
            sig_data = sig_data.split(",", 1)[1]
        session.action_save_signature(sig_data)
        return self._render(
            "l10n_si_kiosk.done",
            {
                "config": session.config_id,
                "session": session,
                "token": token,
            },
        )

    @http.route("/kiosk/cancel", type="http", auth="public", website=True)
    def kiosk_cancel(self, token, **kw):
        """Guest cancelled — return to welcome."""
        session = self._get_session(token)
        if session:
            session.action_abandon()
        return request.redirect("/kiosk/start")

    @http.route("/kiosk/health", type="json", auth="public", website=True)
    def kiosk_health(self, **kw):
        """Health check endpoint for monitoring."""
        config_count = request.env["l10n_si.kiosk.config"].search_count(
            [("active", "=", True)]
        )
        return {"status": "ok", "active_configs": config_count}

    # ----- Helpers --------------------------------------------------------
    def _extract_review_data(self, kw):
        """Extract review form fields from request params."""
        fields_map = [
            "guest_first_name", "guest_last_name", "guest_nationality",
            "guest_doc_number", "guest_address", "guest_city",
            "guest_email", "guest_phone", "arrival_time",
        ]
        data = {f: kw.get(f, "").strip() for f in fields_map}
        # Numeric fields
        for f in ["adults_count", "children_count"]:
            try:
                data[f] = int(kw.get(f, 1) or 1)
            except (ValueError, TypeError):
                data[f] = 1
        # Date field
        if kw.get("guest_birth_date"):
            data["guest_birth_date"] = kw["guest_birth_date"]
        # Selection fields
        if kw.get("guest_doc_type"):
            data["guest_doc_type"] = kw["guest_doc_type"]
        if kw.get("guest_gender"):
            data["guest_gender"] = kw["guest_gender"]
        if kw.get("guest_country_id"):
            try:
                data["guest_country_id"] = int(kw["guest_country_id"])
            except (ValueError, TypeError):
                pass
        return data
