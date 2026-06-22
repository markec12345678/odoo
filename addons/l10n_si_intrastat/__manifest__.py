# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Intrastat',
    'summary': 'Mesečno poročilo Intrastat za trgovino z EU',
    'version': '19.0.1.0.0',
    'category': 'Slovenian Localization',
    'description': "Mesečno poročilo Intrastat za trgovino z EU.",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['account', 'l10n_si'],
    'data': [
        'security/ir.model.access.csv',
        'data/l10n_si_intrastat_data.xml',
        'views/l10n_si_intrastat_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
