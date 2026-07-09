# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Payroll (Community)',
    'summary': 'Slovenian payroll: ZDoh-2, ZPrD, M4, REK-SH, olajšave, letni obračun',
    'version': '19.0.1.0.1',
    'category': 'Accounting/Localizations/Payroll',
    'description': """
Slovenian Payroll (Community Edition)
======================================

Free open-source Slovenian payroll module for Odoo Community 19.0.
Replaces the Enterprise `l10n_si_hr_payroll` module.

Features
--------
* Slovenian contributions (Prispevki):
  - Employer 16.10%: pokojninsko 8.85%, zdravstveno 6.36%, starševsko 0.36%,
    brezposelnost 0.06%, poškodbe 0.53%
  - Employee 22.10%: pokojninsko 15.50%, zdravstveno 6.36%, starševsko 0.10%,
    brezposelnost 0.14%
* Income tax prepayment (Akontacija dohodnine) — ZDoh-2:
  - 16% do 8.500 €
  - 26% 8.500–25.000 €
  - 33% 25.000–36.000 €
  - 39% 36.000–70.000 €
  - 50% > 70.000 €
* Tax relief (Olajšave):
  - Splošna (3.500 € letno)
  - Za otroke (1.124,88–3.374,64 € glede na število)
  - Invalidska (2.250 €)
  - Za dijaka/študenta (2.250 €)
  - Za mladega delojemalca (3.500 €) — special incentive
* Annual reconciliation (Letni obračun)
* Sick leave (Bolniška) — nadomestila
* M4 monthly report (auto-generated via `l10n_si_reports`)
* REK-1 employee registration
* Payslip PDF (slovenian format)
* Multi-company

Legal basis
-----------
* ZDoh-2 (Zakon o dohodnini)
* ZPrD (Zakon o prispevkih za socialna varstva)
* ZInfZoh (olajšave, 109. člen ZDoh-2)
* Pravilnik o obračunu in odvedbi akontacije dohodnine

License: LGPL-3.0
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': [
        'hr',
        'hr_holidays',
        'account',
        'l10n_si',
        'l10n_si_vat_validation',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/l10n_si_payroll_constants_data.xml',
        'data/l10n_si_payroll_cron_data.xml',
        'views/l10n_si_payroll_structure_views.xml',
        'views/l10n_si_payslip_views.xml',
        'views/hr_employee_views.xml',
        'views/res_company_views.xml',
        'wizard/l10n_si_payslip_run_wizard_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'countries': ['si'],
    'qweb': [
        'reports/l10n_si_payslip_report.xml',
    ],
}