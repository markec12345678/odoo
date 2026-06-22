# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Tourist Tax (Turistična taksa)',
    'summary': 'Promocijska taksa po občinah - obračun, naplačilo, eDavki poročilo',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Localizations',
    'description': """
Slovenian Tourist Tax (Turistična taksa)
=========================================

Implements the Slovenian **promocijska taksa** (tourist tax) per ZTur-1
(Zakon o spodbujanju razvoja turizma, UR. l. RS š. 8/17).

Features
--------
* Per-municipality (občina) tax rates — each Slovenian municipality sets its own
* Per-person-per-night calculation
* Age exemptions (children under 7 free, 7-18 reduced)
* Duration cap: maximum 7 nights charged (some municipalities differ)
* Auto-add tax line to hotel/camping/farm folio invoices
* Monthly/quarterly reporting to municipality
* Excel + XML export for eDavki
* Audit trail of all tax collected

Municipality rates
------------------
Each Slovenian municipality (212 total) sets its own rate via občinski odlok.
Typical range: 1.00 - 2.50 EUR per person per night.

Integrations
------------
* `l10n_si_hotel` - hotel folios
* `l10n_si_camping` - camping reservations
* `l10n_si_farm_tourism` - farm stays
* `l10n_si_reports` - M-TAX report (custom report type)

Legal basis
-----------
* ZTur-1 (UR. l. RS š. 8/17, 26/19, 46/19)
* Pravilnik o spodbujanju razvoja turizma
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'l10n_si',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/tourist_tax_data.xml',
        'views/l10n_si_tourist_tax_municipality_views.xml',
        'views/l10n_si_tourist_tax_transaction_views.xml',
        'views/l10n_si_tourist_tax_report_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'countries': ['si'],
}
