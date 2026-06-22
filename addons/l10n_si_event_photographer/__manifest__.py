# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Event Photographer/DJ Booking',
    'summary': 'Zunanji izvajalci - fotograf, DJ, glasba, cvetje, dekoracija',
    'version': '19.0.1.0.0',
    'category': 'Event Management',
    'description': """
Slovenian Event Photographer/DJ Booking
========================================

Upravljanje zunanjih izvajalcev za dogodke:
* Fotograf / videoproducent
* DJ / glasba (band)
* Cvetličar
* Dekorater
* Vodja prireditve (MC)
* Vozilo (limuzina za poroke)

Features
--------
* Katalog zunanjih izvajalcev (partnerjev) z njihovimi ceniki
* Avtomatsko naročanje za posamezen dogodek
* Status povpraševanja → potrjeno → izvedeno → plačano
* Povezava z account.move (račun dobavitelja)
* Ocene izvajalcev (rating)
* Zgodovina sodelovanja
* Avtomatsko e-poštno obveščanje ob naročilu
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['l10n_si_event_venue', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/photographer_data.xml',
        'views/l10n_si_event_vendor_views.xml',
        'views/l10n_si_event_vendor_booking_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
