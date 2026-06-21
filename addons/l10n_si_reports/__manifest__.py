# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Slovenian Regulatory Reports (AJPES, REK-1, M4)',
    'summary': 'Generate and export AJPES SRS, REK-1, M4 reports in XML for eDavki',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Localizations',
    'description': """
Slovenian Regulatory Reports
=============================

Generates the three mandatory regulatory reports for Slovenian companies:

1. **AJPES SRS** (Standardni računovodski izkaz)
   - Annual financial statement submitted to AJPES by 31 March
   - Required for all d.o.o., s.p., kmetije with revenue > 60.000 €
   - XML format per AJPES SRS schema v3.0

2. **REK-1** (Registracija kupcev — Registration of buyers)
   - Monthly report of all B2B sales with VAT
   - Submitted to FURS by 5th of following month
   - Used to cross-check buyer VAT deductions
   - XML format per FURS REK-1 spec v1.3

3. **M4** (Obračun akontacije dohodnine — Monthly income tax prepayment)
   - Monthly report of employee salary advances
   - Submitted to FURS by 15th of following month
   - Requires `l10n_si_hr_payroll` (or manual entry)
   - XML format per FURS M4 spec v2.1

Features
--------
* Date-range filter (custom or preset: this month, this quarter, this year)
* Multi-company support (each company generates its own report)
* Export to XML (eDavki format) or PDF (preview)
* History log of all generated reports
* Re-generation: previously generated reports are versioned

References
----------
* AJPES Pravilnik o vsebini in obliki računovodskih izkazov (UR. l. RS š. 60/06)
* ZDDV-1, 81. člen (REK-1 obveznost)
* ZDoh-2, 28. člen (M4 obveznost)
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'l10n_si',
        'l10n_si_vat_validation',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/l10n_si_report_log_views.xml',
        'views/l10n_si_report_wizard_views.xml',
        'wizard/l10n_si_ajpes_srs_wizard_views.xml',
        'wizard/l10n_si_rek1_wizard_views.xml',
        'wizard/l10n_si_m4_wizard_views.xml',
        'data/ir_sequence_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'countries': ['si'],
}
