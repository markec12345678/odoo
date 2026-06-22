# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Hotel Transport',
    'summary': 'Hotel shuttle, letališki transferi, izleti z avtobusom',
    'version': '19.0.1.0.0',
    'category': 'Hospitality',
    'description': "Transport za goste: shuttle do letališča, izleti, taxi, najem avta.",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['l10n_si_hotel', 'fleet'],
    'data': [
        'security/ir.model.access.csv',
        'data/transport_data.xml',
        'views/l10n_si_transport_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
