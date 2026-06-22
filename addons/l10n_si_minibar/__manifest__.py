# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Hotel Minibar',
    'summary': 'Upravljanje minibarjev - zaloga, pobiranje, zaračunavanje',
    'version': '19.0.1.0.0',
    'category': 'Slovenian Localization',
    'description': "Upravljanje minibarjev - zaloga, pobiranje, zaračunavanje.",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['l10n_si_hotel', 'stock'],
    'data': ['security/ir.model.access.csv', 'data/l10n_si_minibar_data.xml', 'views/l10n_si_minibar_views.xml'],
    'installable': True, 'application': True, 'auto_install': False,
}
