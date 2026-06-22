# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Laundry Service',
    'summary': 'Pralna služba za goste in interne potrebe',
    'version': '19.0.1.0.0',
    'category': 'Slovenian Localization',
    'description': "Pralna služba za goste in interne potrebe.",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['l10n_si_hotel'],
    'data': ['security/ir.model.access.csv', 'data/l10n_si_laundry_data.xml', 'views/l10n_si_laundry_views.xml'],
    'installable': True, 'application': True, 'auto_install': False,
}
