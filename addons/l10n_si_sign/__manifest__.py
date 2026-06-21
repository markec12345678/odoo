# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Digital Signing (eIDAS)',
    'summary': 'Sign PDF/XML documents with qualified SI-TRUST/CA HALCOM certificates',
    'version': '19.0.1.0.0',
    'category': 'Productivity/Sign',
    'description': """
Slovenian Digital Signing (eIDAS)
==================================

Sign documents (PDF, XML, ODT) with qualified eIDAS certificates issued by
SI-TRUST, CA HALCOM, or SIGEN-CA. Replaces Odoo Enterprise `sign` module
for Slovenian use cases.

Features
--------
* Upload PDF → sign with company eIDAS certificate
* Multi-signature workflow (multiple signers in sequence or parallel)
* Timestamp via trusted TSA (RFC 3161) — provides long-term validity
* Verify signature using public keys from SI-TRUST
* Embed signature in PDF as PAdES-Baseline-B (ETSI EN 319 142-1)
* Sign XML as XAdES-BES
* Audit trail of every signature
* Email signed document back to requester
* Integration with `l10n_si_edi` — sign eSLOG XMLs with same cert

Configuration
-------------
1. Company → SI Sign tab → upload .p12 eIDAS cert (QAQC) + password
2. Optional: configure TSA URL (default: SI-TRUST free TSA at https://tsa.si-trust.gov.si)
3. Configure default signature workflow (parallel vs sequential)

Legal basis
-----------
* eIDAS Regulation (EU 910/2014)
* ZEUPP-1 (Zakon o elektronskem izjavljanju in poslovanju)
* ETSI EN 319 142-1 (PAdES), ETSI EN 319 132-1 (XAdES)
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'l10n_si',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_company_views.xml',
        'views/l10n_si_sign_request_views.xml',
        'wizard/l10n_si_sign_upload_wizard_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'countries': ['si'],
}
