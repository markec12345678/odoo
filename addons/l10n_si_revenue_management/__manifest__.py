# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Revenue Management',
    'summary': 'Dinamično določanje cen (yield management) glede na povpraševanje',
    'version': '19.0.1.0.0',
    'category': 'Hotel Management',
    'description': """
Slovenian Revenue Management
============================

Yield management za hotele:
* Dinamično določanje cen glede na:
  - Zasedenost (višja kot bolj polna, višja cena)
  - Dan v tednu (vikend vs delavnik)
  - Sezona (visoka/nizka/prelivna)
  - Dogodki v bližini (konference, koncerti, prazniki)
  - Čas do prihoda (last-minute dražje, zgodnje ceneje)
  - Konkurenca (spremljanje cen drugih hotelov)
* BAR (Best Available Rate) - osnovna cena
* Rate codes (AAA, korporativne, senior, skupinske)
* Omejitve (min/max nočitev, closed to arrival, closed to departure)
* Avtomatsko pošiljanje cen v channel manager
* Forecast zasedenosti 90 dni vnaprej
* Priporočila za cene z AI
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['l10n_si_hotel', 'l10n_si_camping'],
    'data': [
        'security/ir.model.access.csv',
        'data/revenue_data.xml',
        'data/ir_cron_data.xml',
        'views/l10n_si_rate_plan_views.xml',
        'views/l10n_si_rate_calendar_views.xml',
        'views/l10n_si_occupancy_forecast_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
