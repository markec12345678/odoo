# -*- coding: utf-8 -*-
{
    'name': 'Croatian Fiscal Verification (Fiskalizacija 2.0)',
    'summary': 'Porezna uprava CISF — ZKI generation, JIR submission, QR code',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Localizations',
    'description': """
Croatian Fiscal Verification (Fiskalizacija 2.0)
================================================

Implements **fiskalizacija računa** as required by Zakon o fiskalizaciji
u prometu gotovinom (UR. l. RH š. 133/12, 145/14, 40/19).

Features
--------
* **ZKI** (Zaštitni kod izdavatelja računa) — MD5 hash
* **JIR** (Jedinstveni identifikator računa) — UUID from CISF
* **QR code** on invoice PDF
* **FINA mTLS** certificate authentication
* Multi-environment: DEMO (cistest.apis-it.hr) / PROD (cis.porezna-uprava.gov.hr)

CISF endpoints:
- DEMO: https://cistest.apis-it.hr:8449/FiskalizacijaServiceTest
- PROD: https://cis.porezna-uprava.gov.hr:8449/FiskalizacijaService

References
----------
* Zakon o fiskalizaciji (UR. l. RH š. 133/12, 145/14, 40/19)
* Fiskalizacija — Tehnička specifikacija za korisnike v1.8
* FINA cert: https://cms-test.fina.hr (DEMO) / https://cms.fina.hr (PROD)
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'l10n_hr',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/l10n_hr_fiscal_security.xml',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'views/res_company_views.xml',
        'views/l10n_hr_business_premise_views.xml',
        'views/account_move_views.xml',
        'views/l10n_hr_fiscal_log_views.xml',
        'views/l10n_hr_fiscal_menu.xml',
        'reports/report_invoice_with_zki.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'countries': ['hr'],
}
