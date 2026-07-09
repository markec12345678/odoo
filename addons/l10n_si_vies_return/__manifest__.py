# -*- coding: utf-8 -*-
{
    'name': 'Slovenian VIES Return',
    'summary': 'Mesečni VIES za davčne številke kupcev v EU',
    'version': '19.0.1.0.1',
    'category': 'Slovenian Localization',
    'description': "Mesečni VIES za davčne številke kupcev v EU.",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['account', 'l10n_si'],
    'data': [
        'security/ir.model.access.csv',
        'data/l10n_si_vies_return_data.xml',
        'views/l10n_si_vies_return_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
