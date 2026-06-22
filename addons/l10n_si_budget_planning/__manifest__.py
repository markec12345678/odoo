# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Budget Planning',
    'summary': 'Letni proračun po oddelkih - načrtovanje, spremljanje, odstopanja',
    'version': '19.0.1.0.0',
    'category': 'Accounting',
    'description': """
Slovenian Budget Planning
=========================

Letni proračun hotelskega/turističnega podjetja:
* Po oddelkih: sobe, F&B, wellness, dogodki, hišništvo, vzdrževanje, uprava
* Po mesecih (12 mesečni načrt)
* Po vrstah stroškov: osebje, materiali, energija, marketing, amortizacija
* Po vrstah prihodkov: sobe, F&B, wellness, dogodki, drugo
* Spremljanje realizacije (vsak mesec primerjava z načrtom)
* Odstopanja (variance) v % in EUR
* Letni forecast obnovitve (vsak kvartal posodobi preostali del leta)
* Approval workflow (predlog → pregled → odobritev)
* Povezava z analitiko (account.analytic.account)
* Izvoz v Excel
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['account', 'analytic'],
    'data': [
        'security/ir.model.access.csv',
        'data/budget_data.xml',
        'views/l10n_si_budget_views.xml',
        'views/l10n_si_budget_line_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
