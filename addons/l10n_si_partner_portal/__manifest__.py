# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Partner Portal',
    'summary': 'Gostje vidijo rezervacije, folio, točke zvestobe, prijavo napak',
    'version': '19.0.1.0.0',
    'category': 'Portal',
    'description': "Guest portal for reservations, loyalty, maintenance.",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['portal', 'l10n_si_hotel', 'l10n_si_loyalty_program', 'l10n_si_maintenance_request'],
    'data': [],
    'installable': True, 'application': True, 'auto_install': False,
    'qweb': [
        'views/l10n_si_partner_portal_templates.xml',
    ],
}