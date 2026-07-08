# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Hotel Maintenance Request',
    'summary': 'Gostje prijavijo napake preko portala + interne zahtevke',
    'version': '19.0.1.0.0',
    'category': 'Hotel Management',
    'description': """
Slovenian Hotel Maintenance Request
====================================

Prijave napak in težav:
* Gostje prijavijo napake preko portala (QR koda v sobi)
* Hišnik prijavlja najdene poškodbe
* Recepcija lahko ustvari interno zahtevo
* Tehnična služba vidi seznam + dodeljuje
* Status: prijavljeno → v obravnavi → opravljeno
* Slikovni dokazi
* Kategorije: elektrika, vodovodne, klima, namizje, drugo
* Sla: kritično (1h), visoko (4h), normalno (24h), nizko (7 dni)
* Audit trail
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['l10n_si_hotel', 'l10n_si_housekeeping', 'portal'],
    'data': [
        'security/ir.model.access.csv',
        'views/l10n_si_maintenance_request_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [
        'views/l10n_si_maintenance_portal_templates.xml',
    ],
}