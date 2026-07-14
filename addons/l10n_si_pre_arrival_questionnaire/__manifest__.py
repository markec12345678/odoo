# -*- coding: utf-8 -*-
{
    "name": "SI/HR Pre-arrival Questionnaire",
    "version": "19.0.1.0.0",
    "summary": "Guest fills a pre-arrival survey (dietary, allergies, "
    "activities, preferences) via token-authenticated link. Feeds AI "
    "personalisation and kiosk pre-fill.",
    "description": """
SI/HR Pre-arrival Questionnaire
================================

Lets guests fill a structured pre-arrival survey so the hotel can prepare
a personalised stay before they arrive.

Guest flow:
  1. Guest Journey email (T-7d) includes a unique link
     /questionnaire/start/<token>
  2. Guest opens link — no login required
  3. Multi-step form: dietary, allergies, activities, room prefs, arrival
  4. On submit: data is saved on the folio as JSON + structured fields
  5. Reception sees a "Questionnaire completed" indicator on the folio
  6. Kiosk pre-fills check-in form from questionnaire data
  7. AI Concierge uses preferences to recommend activities

Captured data:
  * Dietary restrictions (vegetarian, vegan, gluten-free, halal, kosher, ...)
  * Allergies (peanuts, lactose, pollen, ...)
  * Pillows (firm / soft, hypoallergenic)
  * Bed configuration (king / twin, extra bed, crib)
  * Floor preference (low / high / quiet)
  * Special occasion (birthday, anniversary, honeymoon)
  * Planned activities (spa, excursion, restaurant, fitness)
  * Arrival details (time, transport, parking needed)
  * Communication preference (email / WhatsApp / SMS)
  * Free-text "anything else?"

Integrates with:
  * l10n_si_hotel          (folio)
  * l10n_si_guest_journey  (link in T-7d email)
  * l10n_si_kiosk          (pre-fill check-in)
  * l10n_si_ai_concierge   (context for personalisation)
  * website                (QWeb templates)
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
        "security/questionnaire_security.xml",
        "data/ir_cron_data.xml",
        "data/questionnaire_demo_data.xml",
        "views/questionnaire_template_views.xml",
        "views/questionnaire_response_views.xml",
        "views/hotel_folio_views.xml",
        "views/questionnaire_templates.xml",
        "views/questionnaire_menus.xml",
        "reports/questionnaire_report.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
