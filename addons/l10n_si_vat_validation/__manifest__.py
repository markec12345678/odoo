# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Slovenian VAT Number Validation',
    'summary': 'Validate Slovenian VAT numbers (davčna številka) with MOD11 + FURS VIES check',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Localizations',
    'description': """
Slovenian VAT Number Validation
================================

Validates Slovenian VAT numbers (davčna številka) at two levels:

1. **Format validation (offline)** — verifies the 8-digit SI format and the
   MOD11 checksum used by FURS. Invalid numbers are rejected before save.
2. **Existence validation (online, optional)** — queries the FURS REST API
   (PrObračun DAV-POT) to confirm the VAT number is registered and active.

Configuration:
    * Settings → Accounting → Slovenian VAT Validation
    * Enable "Check VAT with FURS" and set the endpoint
      (test: https://blagajne-test.fu.gov.si, prod: https://blagajne.fu.gov.si)
    * Requires a valid FURS certifikate (.p12) configured in the company

References:
    * ZDavR-1, 23. člen — davčna številka
    * FURS PrObračun DAV-POT API spec, v1.0
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': [
        'base_vat',
        'l10n_si',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/res_company_data.xml',
        'views/res_company_views.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'countries': ['si'],
}
