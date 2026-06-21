# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Fleet Management',
    'summary': 'Vehicle fleet with SI-specific: tehnični pregled, zavarovanje, gorivo, vozni listi',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Fleet',
    'description': """
Slovenian Fleet Management
===========================

Vehicle fleet management with Slovenian-specific features.

Features
--------
* Vehicle registry (vozila) with SI-specific fields:
  - Registrska tablica (LP-123-AB)
  - Številka šasije (VIN)
  - Številka motorja
  - Leto proizvodnje
  - Tip goriva (bencin, dizel, hibrid, električni, plin)
  - Poraba (l/100km ali kWh/100km)
* Tehnični pregled (MOT) — reminders 30/7 days before expiration
* Zavarovanje (insurance) — AO, KASKO, with renewal reminders
* Registracija — annual vehicle registration renewal
* Vozni listi (trip logs) — start/end mileage, driver, purpose
* Gorivo (fuel logs) — volume, price, fuel station, total cost
* Servisi (maintenance) — scheduled and ad-hoc, with cost tracking
* Stroški po vozilu (costs per vehicle) — fuel + service + insurance + registration
* Drivers (vozniki) — link to hr.employee
* Dashboard: monthly cost per vehicle, fuel efficiency trends

SI-specific reminders
---------------------
* 30 days before tehnični pregled expiration → email responsible person
* 30 days before zavarovanje expiration → email finance
* 30 days before registracija expiration → email fleet manager

Legal references
----------------
* ZPrCP (Zakon o pravilih cestnega prometa) — tehnični pregledi
* ZZavar (Zakon o obveznem zavarovanju) — AO zavarovanje
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'hr',
        'fleet',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/l10n_si_fleet_vehicle_views.xml',
        'views/l10n_si_fleet_trip_views.xml',
        'views/l10n_si_fleet_fuel_views.xml',
        'views/l10n_si_fleet_maintenance_views.xml',
        'views/l10n_si_fleet_insurance_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'countries': ['si'],
}
