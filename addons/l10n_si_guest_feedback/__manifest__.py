# -*- coding: utf-8 -*-
{
    "name": "SI/HR Guest Feedback — Real-time",
    "version": "19.0.1.0.0",
    "summary": "Real-time in-stay and post-stay guest feedback with instant "
    "low-score alerts. Token-based (no login). Triggers SMS/email/WhatsApp "
    "to manager when score < threshold.",
    "description": """
SI/HR Guest Feedback — Real-time
================================

Collects structured feedback from guests during their stay and after
checkout, with real-time alerting when scores are low.

Use cases:
  * Day 1 evening: "How was your arrival?" (1-5 stars)
  * Mid-stay: "Rate your room / breakfast / service"
  * Post-stay: NPS survey (would you recommend us?)
  * Trigger: any score <= 2 sends instant alert to manager

Guest flow:
  1. Guest receives WhatsApp/email/SMS with unique feedback link
  2. Opens link — no login required (token-authenticated)
  3. Multi-question form (rating + free text)
  4. On submit: data saved + dashboard updated in real-time
  5. If any score <= threshold (default 2): instant alert to manager
     via email + WhatsApp + internal chat notification

Key features:
  * Token-based, no login (works on any device)
  * 5-star rating + free-text comment per question
  * Configurable alert threshold (default: score <= 2 triggers alert)
  * Multi-channel alerts: email, WhatsApp, internal chat
  * Real-time dashboard (auto-refresh every 30s)
  * Sentiment analysis via AI Core (optional)
  * Trends: score over time, by room type, by staff member
  * Action tracking: each alert can be assigned and resolved
  * GDPR-safe: feedback can be anonymous

Integrates with:
  * l10n_si_hotel (folio lookup)
  * l10n_si_guest_journey (link in mid-stay message)
  * l10n_si_whatsapp_business (alert channel)
  * l10n_si_ai_core (sentiment analysis, optional)
  * website (QWeb templates)
""",
    "author": "SI/HR Tourism Suite",
    "website": "https://github.com/markec12345678/odoo-si-hr-tourism-suite",
    "license": "LGPL-3",
    "category": "Hospitality/Guest Experience",
    "depends": [
        "l10n_si_hotel",
        "website",
        "mail",
    ],
    "external_dependencies": {
        "python": [],
    },
    "data": [
        "security/ir.model.access.csv",
        "security/guest_feedback_security.xml",
        "data/ir_cron_data.xml",
        "data/feedback_demo_data.xml",
        "views/feedback_survey_views.xml",
        "views/feedback_response_views.xml",
        "views/feedback_alert_views.xml",
        "views/feedback_dashboard_views.xml",
        "views/hotel_folio_views.xml",
        "views/feedback_templates.xml",
        "views/feedback_menus.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
