# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Maintenance (Advanced)',
    'summary': 'Preventive + corrective maintenance with MTBF tracking and spare parts',
    'version': '19.0.1.0.0',
    'category': 'Maintenance',
    'description': """
Slovenian Maintenance Advanced
===============================

Extends standard `maintenance` module with:
* Preventive maintenance schedules (weekly/monthly/yearly per equipment)
* MTBF (Mean Time Between Failures) tracking
* MTTR (Mean Time To Repair) tracking
* Spare parts inventory per equipment
* Maintenance team scheduling
* Cost tracking per equipment
* Equipment downtime analysis
* Integration with stock for parts consumption

Replaces Enterprise `maintenance` extensions.
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['maintenance', 'stock', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/maintenance_equipment_views.xml',
        'views/l10n_si_maintenance_schedule_views.xml',
        'views/maintenance_request_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
