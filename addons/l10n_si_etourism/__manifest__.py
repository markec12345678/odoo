# -*- coding: utf-8 -*-
{
    'name': 'Slovenian eTurizem (AJPES Guest Registration)',
    'summary': 'Prijava in odjava gostov prek AJPES eTurizem (ZPPreb-1, ZTur-1)',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Localizations',
    'description': """
Slovenian eTurizem (AJPES Guest Registration)
==============================================
Implements mandatory guest registration with AJPES eTurizem web service per
ZPPreb-1 (Zakon o prijavi prebivališča, UR. l. RS š. 81/16) and ZTur-1.
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'l10n_si',
        'l10n_si_hotel',
        'l10n_si_camping',
        'l10n_si_tourist_tax',
    ],
    'data': [
        'security/l10n_si_etourism_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',
        'views/l10n_si_etourism_establishment_views.xml',
        'views/l10n_si_etourism_guest_registration_views.xml',
        'views/l10n_si_etourism_log_views.xml',
        'views/res_company_views.xml',
        'views/l10n_si_etourism_menu.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'countries': ['si'],
}
