# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Concierge Services',
    'summary': 'Concierge desk - izleti, vstopnice, rezervacije, priporočila',
    'version': '19.0.1.0.0',
    'category': 'Hospitality',
    'description': "Concierge desk za goste: izleti, vstopnice, restavracije, prevozi, lokalna priporočila.",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['l10n_si_hotel'],
    'data': [
        'security/ir.model.access.csv',
        'data/concierge_data.xml',
        'views/l10n_si_concierge_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
