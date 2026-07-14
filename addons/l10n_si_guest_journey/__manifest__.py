# -*- coding: utf-8 -*-
{
    "name": "SI/HR Guest Journey Orchestrator",
    "version": "19.0.1.0.0",
    "summary": "Automated pre-arrival / in-stay / post-stay guest communication sequences "
    "(email + WhatsApp). Multi-language. AI-personalised.",
    "description": """
SI/HR Guest Journey Orchestrator
================================

Orchestrates the full guest communication lifecycle:

  1. **Pre-arrival**  — 7 days before check-in: "We can't wait to welcome you"
                       — 24h before:  digital guide, parking, WiFi, self check-in link
                       — 0h:           "Your room is ready" (AI Concierge personalised)

  2. **In-stay**      — Day 1 evening: "How was your arrival?"
                       — Day 2:        upsell (spa, breakfast, excursion)
                       — Mid-stay:     "Anything we can do better?"

  3. **Post-stay**    — Day +1:        "Thank you for staying"
                       — Day +3:        review request (Google / Booking.com)
                       — Day +7:        loyalty offer for next stay

Key features:
  * Multi-language templates (SL / EN / HR / DE / IT)
  * Channel: email (default) or WhatsApp Business (if installed)
  * Personalisation via Jinja2 ({{ guest_name }}, {{ room }}, {{ check_in }})
  * AI-personalisation hook: optional `ai_personalize=True` enriches template
    via l10n_si_ai_core (uses guest history, preferences, weather).
  * Per-folio journey visualisation (kanban of upcoming steps)
  * Manual "Send now" override per step
  * Daily cron at 08:00 sends all due steps
  * GDPR-safe: respects `marketing_emails_opt_out` on partner

Integrates with:
  * l10n_si_hotel          (folio model)
  * l10n_si_whatsapp_business (channel)
  * l10n_si_ai_core        (personalisation)
  * l10n_si_partner_portal (self check-in link)
""",
    "author": "SI/HR Tourism Suite",
    "website": "https://github.com/markec12345678/odoo-si-hr-tourism-suite",
    "license": "LGPL-3",
    "category": "Hospitality/Guest Experience",
    "depends": [
        "l10n_si_hotel",
        "mail",
    ],
    "external_dependencies": {
        "python": [],
    },
    "data": [
        "security/ir.model.access.csv",
        "security/guest_journey_security.xml",
        "data/guest_journey_demo_templates.xml",
        "data/ir_cron_data.xml",
        "views/guest_journey_template_views.xml",
        "views/guest_journey_step_views.xml",
        "views/hotel_folio_views.xml",
        "views/guest_journey_menus.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
