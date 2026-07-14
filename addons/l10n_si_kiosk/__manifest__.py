# -*- coding: utf-8 -*-
{
    "name": "SI/HR Kiosk Mode — Lobby Self Check-in",
    "version": "19.0.1.0.0",
    "summary": "Tablet-friendly self check-in kiosk for hotel lobbies. "
    "Scans passport/ID, fills eTurizem registration, prints key card info.",
    "description": """
SI/HR Kiosk Mode — Lobby Self Check-in
======================================

A touch-optimised self check-in kiosk for hotel lobbies. Designed to run
on a wall-mounted tablet (iPad / Android) in the reception area.

Guest flow:
  1. Welcome screen — guest taps "Start check-in"
  2. Lookup — guest enters booking reference OR scans QR code from
     confirmation email
  3. Booking confirmation — guest sees their reservation, taps "Confirm"
  4. Document scan — guest scans passport/ID on attached scanner
     (uses l10n_si_document_scan OCR + MRZ fallback if installed)
  5. Data review — pre-filled form, guest corrects/confirmes
  6. Signature — guest signs on screen (signature pad)
  7. Done — kiosk shows room number, Wi-Fi, breakfast time, key card
     AJPES eTurizem registration is created automatically
     Reception gets a notification

Key features:
  * Touch-optimised UI (large buttons, simple language, multi-language)
  * No login required (token-based access)
  * Session tracking — every kiosk interaction is logged
  * Idle timeout returns to welcome screen after 60s
  * Branded with hotel logo and colors
  * Accessibility mode (high contrast, larger text)
  * Reception dashboard shows active/completed sessions
  * Works offline (queue submissions when network drops)

Integrates with:
  * l10n_si_hotel          (folio lookup)
  * l10n_si_document_scan  (passport OCR + MRZ)
  * l10n_si_etourism       (AJPES guest registration)
  * l10n_si_partner_portal (reuses self check-in logic)
  * website                (for QWeb templates)
""",
    "author": "SI/HR Tourism Suite",
    "website": "https://github.com/markec12345678/odoo-si-hr-tourism-suite",
    "license": "LGPL-3",
    "category": "Hospitality/Guest Experience",
    "depends": [
        "l10n_si_hotel",
        "website",
    ],
    "external_dependencies": {
        "python": [],
    },
    "data": [
        "security/ir.model.access.csv",
        "security/kiosk_security.xml",
        "data/ir_cron_data.xml",
        "data/kiosk_demo_data.xml",
        "views/kiosk_session_views.xml",
        "views/kiosk_config_views.xml",
        "views/kiosk_menus.xml",
        "views/kiosk_templates.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
