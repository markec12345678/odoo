# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Slovenian eInvoice (eSLOG 2.0)',
    'summary': 'FURS eDavki submission of eSLOG 2.0 XML invoices (B2B/B2G)',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Localizations',
    'description': """
Slovenian eInvoice (eSLOG 2.0)
===============================

Generates and submits **eSLOG 2.0** XML invoices to FURS eDavki portal as
required by:
* ZEfUP (Zakon o elektronskem fakturowanju v javnem sektorju) — B2G mandatory from 2025
* EU Directive 2014/55/EU — European standard EN 16931
* Slovenian B2B e-invoicing rollout (postopeno do 2027)

Features
--------
* Generate eSLOG 2.0 XML (UBL-based, SI profile) for `account.move`
* Submit via FURS eDavki REST API with eIDAS qualified certificate
* Track submission status (draft / sent / accepted / rejected)
* Store signed XML as attachment (10-year retention per ZDavR-1)
* Reverse charge handling (Article 79)
* VAT exemption handling (Article 25, 26, 43, 46, 47)
* Credit notes (storno) with reference to original invoice

Configuration
-------------
1. Company → e-Račun tab: upload eIDAS qualified .p12 certificate (SI-TRUST / CA HALCOM)
2. Set endpoint: TEST (edavki-test.fu.gov.si) or PROD (edavki.fu.gov.si)
3. Set the company's PEPPOL identifier (SI + davčna številka)
4. Enable auto-submit on invoice posting (optional)

References
----------
* FURS eDavki technical specification v2.0
* eSLOG 2.0 schema: https://www.gzs.si/ebcgs/slog-20
* EN 16931 European e-invoicing standard
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'account_edi_ubl_cii',
        'l10n_si',
        'l10n_si_vat_validation',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/res_company_views.xml',
        'views/account_move_views.xml',
        'views/l10n_si_edi_log_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'countries': ['si'],
}
