# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Loyalty Program',
    'summary': 'Program zvestobe - točke, nivoji (Silver/Gold/Platinum), nagrade',
    'version': '19.0.1.0.0',
    'category': 'Customer Relationship',
    'description': """
Slovenian Loyalty Program
=========================

Program zvestobe za povratne goste:
* Akumulacija točk glede na porabo
* Nivoji: Bronze (0-999), Silver (1000-4999), Gold (5000-19999), Platinum (20000+)
* Popusti glede na nivo:
  - Bronze: 0% popust, dobrodošla pijača
  - Silver: 5% popust, pozna odjava
  - Gold: 10% popust, brezplačen zajtrk
  - Platinum: 15% popust, upgrade sobe, brezplačno wellness
* Nagrade (redemption):
  - 1000 točk = 1 brezplačna nočitev (Standard)
  - 500 točk = brezplačna masaža
  - 200 točk = brezplačno večerja za 2
* Akcije (2x točke ob rojstnem dnevu, 3x v nizki sezoni)
* Portalski pregled stanja za goste
* Pošiljanje kartice po pošti (PDF + fizična)
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['account', 'l10n_si_hotel'],
    'data': [
        'security/ir.model.access.csv',
        'data/loyalty_data.xml',
        'views/l10n_si_loyalty_member_views.xml',
        'views/l10n_si_loyalty_reward_views.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
