# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Weather Integration',
    'summary': 'Vremenska napoved 14 dni',
    'version': '19.0.1.0.0',
    'category': 'Slovenian Localization',
    'description': "Vremenska napoved 14 dni.",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['l10n_si_hotel'],
    'data': ['security/ir.model.access.csv', 'data/l10n_si_weather_integration_data.xml', 'views/l10n_si_weather_integration_views.xml'],
    'installable': True, 'application': True, 'auto_install': False,
}
