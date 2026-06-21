# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Slovenian Fiscal Verification (ZOI/EOR)',
    'summary': 'FURS davčno potrjevanje računov — ZOI generation, EOR submission, QR code',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Localizations',
    'description': """
Slovenian Fiscal Verification (ZOI / EOR)
==========================================

Implements **davčno potrjevanje računov** as required by ZDavPR-1 (Zakon o
davčnem potrjevanju računov, UR. l. RS š. 89/16) for all cash and non-cash
invoices issued to private persons.

Features
--------
* **ZOI** (Zaščitna oznaka izdajatelja računa) — MD5 signature generated from:
  tax_number + issue_datetime + invoice_number + business_premise_id +
  electronic_device_id + invoice_serial_number
* **EOR** (Enkratna identifikacijska oznaka računa) — UUID returned by FURS
  after successful submission via SOAP API over HTTPS with mutual TLS auth
* **QR code** on the invoice PDF containing the ZOI + meta fields
* **Offline mode** — if FURS is unreachable, ZOI is generated locally and the
  invoice is queued for submission (must be sent within 48h per ZDavPR-1)
* **Storno** — credit notes automatically get their own ZOI/EOR with storno flag
* **POS integration** — `pos.order` extended to issue ZOI/EOR at order validation
* Multi-environment: TEST (blagajne-test.fu.gov.si) / PROD (blagajne.fu.gov.si)

Configuration
-------------
1. Company → Fiscal tab: upload FURS-issued .p12 certificate + password
2. Set environment: TEST or PROD
3. Register each business premise via l10n_si_sequence (action_register_with_furs)
4. Settings → Accounting → "Auto-submit to FURS" (default: True)

References
----------
* ZDavPR-1 (UR. l. RS š. 89/16, 13. člen)
* FURS Technical specification for fiscal verification, v1.6
* FURS test portal: https://blagajne-test.fu.gov.si:9002/v1/cash_registers/
* FURS prod portal: https://blagajne.fu.gov.si:9002/v1/cash_registers/

Penalty
-------
Failure to obtain EOR within 48h of issuing a cash invoice is subject to a
fine between 200 € and 125.000 € (ZDavPR-1, 35. člen).
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'l10n_si',
        'l10n_si_sequence',
        'l10n_si_vat_validation',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'views/res_company_views.xml',
        'views/l10n_si_business_premise_views.xml',
        'views/account_move_views.xml',
        'views/l10n_si_fiscal_log_views.xml',
        'wizard/l10n_si_fiscal_resubmit_views.xml',
        'reports/report_invoice_with_zoi.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'countries': ['si'],
}
