# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Fixed Assets',
    'summary': 'Osnovna sredstva z SI amortizacijo (linearna/degresivna per ZDD-1)',
    'version': '19.0.1.0.1',
    'category': 'Accounting/Localizations',
    'description': "Slovenian fixed assets: linear/declining depreciation per ZDD-1, asset categories, disposal, revaluation.",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['account', 'l10n_si'],
    'data': [
        'security/ir.model.access.csv',
        'data/asset_data.xml',
        'views/l10n_si_assets_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
