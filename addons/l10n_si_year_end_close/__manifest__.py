# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Year-End Close',
    'summary': 'Zaključna konta po SRS (konti 990, 999)',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Localizations',
    'description': "Year-end closing per SRS (accounts 990, 999).",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['account', 'l10n_si'],
    'data': ['security/ir.model.access.csv', 'data/l10n_si_year_end_close_data.xml', 'views/l10n_si_year_end_close_views.xml'],
    'installable': True, 'application': True, 'auto_install': False,
}
