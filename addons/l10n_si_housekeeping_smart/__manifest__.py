# -*- coding: utf-8 -*-
{
    "name": "SI/HR Smart Housekeeping Scheduler",
    "version": "19.0.1.0.0",
    "summary": "AI-driven housekeeping scheduling: auto-generates tasks on "
    "check-out, predicts turnover time, balances workload across "
    "housekeepers, optimizes task sequence.",
    "description": """
SI/HR Smart Housekeeping Scheduler
==================================

Extends `l10n_si_housekeeping` with intelligent scheduling:

1. **Auto-generate tasks on check-out** — when a guest checks out, a
   turnover cleaning task is automatically created with the right priority
   based on the next check-in time.

2. **Turnover time prediction** — based on room type (suite vs standard),
   occupancy duration, number of guests, and historical data.

3. **Workload balancing** — distributes tasks across housekeepers based
   on their current load, skills, and language.

4. **Priority-based sequencing** — tasks are sorted by:
   a. Next check-in urgency (next guest arriving in <2h = critical)
   b. VIP guests
   c. Special requests from pre-arrival questionnaire
   d. Room type (suites first)

5. **AI Core integration (optional)** — uses AI to optimize the daily
   task sequence based on:
   - Room locations (group by floor to minimize walking)
   - Housekeeper's current location
   - Special instructions
   - Predicted duration vs scheduled start

6. **Mobile-friendly dashboard** — housekeepers see their daily list
   on a phone, mark tasks done, flag issues.

7. **KPIs** — average turnover time, on-time completion rate, tasks per
   housekeeper per day.

Integrates with:
  * l10n_si_housekeeping (extends task model)
  * l10n_si_hotel (folio, reservation, room)
  * l10n_si_pre_arrival_questionnaire (special requests)
  * l10n_si_ai_core (optional optimization)
""",
    "author": "SI/HR Tourism Suite",
    "website": "https://github.com/markec12345678/odoo-si-hr-tourism-suite",
    "license": "LGPL-3",
    "category": "Hospitality/Operations",
    "depends": [
        "l10n_si_housekeeping",
        "l10n_si_hotel",
        "hr",
    ],
    "external_dependencies": {
        "python": [],
    },
    "data": [
        "security/ir.model.access.csv",
        "security/housekeeping_smart_security.xml",
        "data/ir_cron_data.xml",
        "data/housekeeping_smart_config.xml",
        "views/housekeeping_task_views.xml",
        "views/housekeeping_team_views.xml",
        "views/housekeeping_dashboard_views.xml",
        "views/hotel_room_views.xml",
        "views/hotel_folio_views.xml",
        "views/housekeeping_menus.xml",
        "wizard/generate_tasks_wizard_views.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
