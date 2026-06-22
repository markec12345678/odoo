# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Gift Voucher',
    'summary': 'Darilni vavčerji - prodaja, odkup, sledenje',
    'version': '19.0.1.0.0',
    'category': 'Slovenian Localization',
    'description': "Darilni vavčerji - prodaja, odkup, sledenje.",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['account', 'l10n_si_hotel'],
    'data': ['security/ir.model.access.csv', 'data/l10n_si_gift_voucher_data.xml', 'views/l10n_si_gift_voucher_views.xml'],
    'installable': True, 'application': True, 'auto_install': False,
}
