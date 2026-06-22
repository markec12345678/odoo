# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Data Protection (GDPR)',
    'summary': 'GDPR skladnost za SI - soglasja, hramba, brisanje, IPP',
    'version': '19.0.1.0.0',
    'category': 'Data Protection',
    'description': "GDPR skladnost: upravljanje soglasij, hramba podatkov, pravica do brisanja, IPP prijava.",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/data_protection_data.xml',
        'views/l10n_si_gdpr_consent_views.xml',
        'views/l10n_si_gdpr_request_views.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
