# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Channel Manager',
    'summary': 'Sinhronizacija razpoložljivosti in cen z Booking.com, Airbnb, Expedia',
    'version': '19.0.1.0.0',
    'category': 'Hotel Management',
    'description': """
Slovenian Channel Manager
=========================

Dvosmerna sinhronizacija z:
* Booking.com (preko XML API-ja)
* Airbnb (preko Airbnb API)
* Expedia (preko EQC API)
* Glamping.com (preko REST)

Features
--------
* Avtomatsko pošiljanje razpoložljivosti (Availability push)
* Avtomatsko prejemanje rezervacij (Reservation pull)
* Sinhronizacija cen (Rate push)
* Preprečevanje dvojnih rezervacij (overbookings)
* Cron job vsakih 15 min
* Webhook endpoint za takojšnje posodobitve
* Per-channel pricing (različne cene na različnih kanalih)
* Spremembe statusa (Confirmed → Cancelled) se sinhronizirajo

Zahteva:
* API ključi od vsakega kanala posebej
* Mapiranje med SI sobami in channel room_type_id
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['l10n_si_hotel', 'l10n_si_camping'],
    'data': [
        'security/ir.model.access.csv',
        'data/channel_manager_data.xml',
        'views/l10n_si_channel_config_views.xml',
        'views/l10n_si_channel_log_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
