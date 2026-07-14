# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Partner Portal + Self Check-in',
    'summary': 'Gostje vidijo rezervacije, folio, self check-in, digitalni vodič, upsell',
    'version': '19.0.1.1.0',
    'category': 'Portal',
    'description': """
Guest portal with self check-in, inspired by eGost.si.

Features:
* Self check-in — guest fills personal data before arrival
* Document upload (for OCR scanning if l10n_si_document_scan installed)
* eTurizem auto-registration from portal
* Upsell page (late checkout, airport transfer, breakfast)
* Digital welcome guide (WiFi, house rules, local tips)
* Existing: reservation view, loyalty points, maintenance tickets
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo-si-hr-tourism-suite',
    'license': 'LGPL-3',
    'depends': ['portal', 'l10n_si_hotel', 'l10n_si_loyalty_program', 'l10n_si_maintenance_request'],
    'data': [
        'views/partner_portal_templates.xml',
    ],
    'installable': True, 'application': True, 'auto_install': False,
}