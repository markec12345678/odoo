# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Field Service',
    'summary': 'Work orders + dispatching for field technicians (serviserji, čistilci, vzdrževalci)',
    'version': '19.0.1.0.0',
    'category': 'Services/Field Service',
    'description': """
Slovenian Field Service
========================

Manage field service operations:
* Delovni nalogi (work orders) — assigned to technicians
* Razporejanje (dispatching) — daily route planning
* Sledenje GPS — track technician location
* Mobilni dostop — technicians see assignments on phone
* Časovni listi — start/stop timer on each task
* Material usage — log parts consumed on site
* Podpis stranke — customer signs on completion (touch screen)
* Photo attachments — before/after photos
* Po-obdelava — auto-generate invoice from work order

Replaces Enterprise `fieldservice`.
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'hr', 'stock', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [
        'views/l10n_si_field_service_order_views.xml',
    ],
}