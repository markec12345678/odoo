# -*- coding: utf-8 -*-
{
    'name': 'Croatia — PDV Reporting (ePorezna)',
    'summary': 'Croatian VAT (PDV) reporting: Knjiga PDV-a, PDV obrazac, ePorezna XML',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Localizations',
    'description': """
Croatia — PDV Reporting (ePorezna)
==================================

Implements Croatian VAT (PDV) periodic reporting as required by
Porezna uprava (Tax Administration of the Republic of Croatia).

Features
--------
* **PDV report** (l10n_hr.pdv.report) — monthly or quarterly VAT report
  per company, with VAT breakdown by rate (25% / 13% / 5%).
* **Knjiga PDV-a** (VAT ledger) — detailed per-invoice line items
  (l10n_hr.pdv.report.line) for both output and input VAT.
* **PDV obrazac** — printable PDF form (QWeb) matching the official
  Porezna uprava layout.
* **ePorezna XML** — generates <PdvObrazac> XML ready for upload to the
  ePorezna web portal or for CISF submission.
* **EU partner detection** — automatically identifies EU acquisitions
  (intra-Community acquisitions) and EU supplies (intra-Community
  supplies) based on partner country code (excluding HR).
* **Reverse charge** — detects domestic reverse-charge transactions
  and reports them separately.
* **Cron automation** — auto-generates monthly PDV reports on the
  1st day of each month for the previous period.

VAT rates (Croatia)
-------------------
* 25% — standard rate (opća stopa)
* 13% — reduced rate (snižena stopa)
* 5%  — special reduced rate (posebno snižena stopa)

EU country codes (excluding HR)
-------------------------------
AT, BE, BG, CY, CZ, DE, DK, EE, ES, FI, FR, GR, HU, IE, IT,
LT, LU, LV, MT, NL, PL, PT, RO, SE, SI, SK

Deadlines
---------
* Monthly reporters: 20th of the next month
* Quarterly reporters: 20th after quarter end

References
----------
* Zakon o porezu na dodanu vrijednost (N.N. 73/13, ...)
* Pravilnik o PDV obrascu (ePorezna)
* https://porezna.gov.hr/eporezna
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'l10n_hr',
        'l10n_hr_fiscal',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'views/l10n_hr_pdv_report_views.xml',
        'views/account_move_views.xml',
        'views/l10n_hr_pdv_menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'countries': ['hr'],
    'qweb': [
        'reports/pdv_ledger_report.xml',
        'reports/pdv_form_report.xml',
    ],
}