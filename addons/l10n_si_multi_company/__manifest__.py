# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Multi-Company',
    'summary': 'Hotelske verige z več podjetji',
    'version': '19.0.1.0.0',
    'category': 'Slovenian Localization',
    'description': "Hotelske verige z več podjetji.",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['base', 'l10n_si_hotel'],
    'data': ['security/ir.model.access.csv', 'data/l10n_si_multi_company_data.xml', 'views/l10n_si_multi_company_views.xml'],
    'installable': True, 'application': True, 'auto_install': False,
}
