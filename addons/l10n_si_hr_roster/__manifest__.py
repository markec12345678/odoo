# -*- coding: utf-8 -*-
{
    'name': 'Slovenian HR Roster',
    'summary': 'Razpored delavnikov - izmene, nadure, dopusti, razporejanje',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'description': """
Slovenian HR Roster
===================

Razpored delavnikov za hotelsko/restavracijsko osebje:
* Izmene (shifts): jutranja, popoldanska, nočna, celodnevna
* Tedenski/mesečni razpored
* Avtomatsko razporejanje glede na:
  - Delovno mesto (recepcija, kuhinja, hišništvo, ...)
  - Delovne izkušnje
  - Želje (preferred shifts)
  - Počitek (min 11h med izmenama)
  - Zakonske omejitve (max 40h/teden, max 8h na dan)
* Nadure (avtomatsko detekcija presežka)
* Dopusti integracija z hr_holidays
* Spremenljivice (zamenjave izmen)
* Mobilna aplikacija (vidijo svoj razpored)
* Prisotnost (check-in/check-out z QR kodo)
* Statistika: uradsno, nadure, dopusti, bolniške
* Skladno s slovenskim ZDR-1 (Zakon o delovnih razmerjih)
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['hr', 'hr_holidays', 'hr_attendance'],
    'data': [
        'security/ir.model.access.csv',
        'data/roster_data.xml',
        'views/l10n_si_roster_shift_views.xml',
        'views/l10n_si_roster_assignment_views.xml',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
