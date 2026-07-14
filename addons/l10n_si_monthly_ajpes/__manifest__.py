# -*- coding: utf-8 -*-
{
    "name": "SI Monthly AJPES eTurizem Report",
    "version": "19.0.1.0.0",
    "summary": "Automated monthly AJPES eTurizem report: aggregates all "
    "guest registrations, generates the official XML/CSV, submits to "
    "AJPES, and archives for audit.",
    "description": """
SI Monthly AJPES eTurizem Report
================================

Automates the monthly reporting obligation to AJPES (Agencija za
javnopravne evidence in storitve) for tourist guest registrations.

Slovenian accommodation providers must submit a monthly summary report
to AJPES by the 5th of the following month, covering:
- All arrivals and departures in the month
- Number of nights per guest
- Citizenship breakdown
- Purpose of visit
- Reservation source

This module:
1. Aggregates all l10n_si.etourism.guest.registration records for a month
2. Generates the official AJPES XML report (TURIZEM format)
3. Generates a CSV summary for human review
4. Optionally submits to AJPES via the existing eTurizem API
5. Archives the report for audit (7-year retention required)
6. Sends email notification to the responsible user with the report attached
7. Cron job runs on the 1st of each month, generates the previous month's report

Key features:
- One-click monthly report generation
- Automatic cron on 1st of each month
- XML + CSV + PDF formats
- Email notification with attachment
- Audit trail (who generated, when, what was submitted)
- Re-generation support (with version tracking)
- Multi-establishment support (one report per establishment)
- Statistics dashboard: arrivals, nights, average stay, top countries

Integrates with:
  * l10n_si_etourism (guest registrations, establishment, API)
  * mail (email notification)
  * report_xlsx (Excel export, optional)
""",
    "author": "SI/HR Tourism Suite",
    "website": "https://github.com/markec12345678/odoo-si-hr-tourism-suite",
    "license": "LGPL-3",
    "category": "Hospitality/Regulatory",
    "depends": [
        "l10n_si_etourism",
        "mail",
    ],
    "external_dependencies": {
        "python": [],
    },
    "data": [
        "security/ir.model.access.csv",
        "security/monthly_ajpes_security.xml",
        "data/ir_cron_data.xml",
        "data/email_template_data.xml",
        "views/monthly_report_views.xml",
        "views/monthly_report_dashboard.xml",
        "views/establishment_views.xml",
        "views/monthly_ajpes_menus.xml",
        "reports/monthly_report_xml_template.xml",
        "reports/monthly_report_pdf_template.xml",
        "wizard/generate_monthly_report_wizard_views.xml",
    ],
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
