# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Executive Dashboard',
    'summary': 'KPI nadzorna plošča za vodstvo - ADR, RevPAR, zasedenost, prihodek',
    'version': '19.0.1.0.0',
    'category': 'Hotel Management',
    'description': """
Slovenian Executive Dashboard
=============================

KPI nadzorna plošča za vodstvo hotelskih/turističnih podjetij:
* Occupancy (zasedenost) - dnevno, mesečno, letno
* ADR (Average Daily Rate) - povprečna cena nočitve
* RevPAR (Revenue Per Available Room) - ključni KPI
* GopPAR (Gross Operating Profit per Available Room)
* Prihodek po segmentih (sobe, F&B, wellness, dogodki)
* Top stranke
* Top sobe (najbolj dobičkonosne)
* Primerjava obdobij (letos vs lani)
* Grafi: line chart zasedenosti, bar chart prihodkov
* Filter: hotel, datumsko obdobje, segment
* Export v Excel
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['l10n_si_hotel', 'l10n_si_restaurant', 'l10n_si_wellness', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/l10n_si_dashboard_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
