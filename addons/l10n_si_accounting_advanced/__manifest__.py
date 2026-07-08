# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Accounting Advanced',
    'summary': 'SRS, bilanca, izid poslovanja, denarni tok, analize',
    'version': '19.0.1.0.0',
    'Category': 'Accounting/Localizations',
    'description': """
Slovenian Accounting Advanced
==============================

Napredna knjigovodska poročila za slovenska podjetja:
* SRS (Slovenski računovodski standardi) poročila:
  - Bilanca stanja (Balance Sheet)
  - Izid poslovanja (Income Statement / Profit & Loss)
  - Poročilo o denarnih tokovih (Cash Flow Statement)
  - Poročilo o spremembah kapitala
* Postavke po SRS klasifikaciji (konti 0xx-9xx)
* Primerjava obdobij (letos vs lani, Q1/Q2/Q3/Q4)
* Vertikalna in horizontalna analiza
* Ključni kazalci (rentabilnost, likvidnost, zadolženost)
* Letni obračun (zaključna konta)
* Davčno knjigovodstvo (knjiga DDV)
* Priprava za AJPES
* Export v Excel/PDF
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['account', 'l10n_si', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'data/accounting_data.xml',
        'data/srs_accounts_data.xml',
        'views/l10n_si_srs_account_views.xml',
        'views/l10n_si_srs_report_views.xml',
        'views/l10n_si_financial_ratio_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [
        'reports/srs_financial_reports.xml',
    ],
}