# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Quality Control',
    'summary': 'Quality inspection points for production orders + supplier deliveries',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing/Quality',
    'description': """
Slovenian Quality Control
=========================

Quality control for:
* Proizvodnja (manufacturing orders) — control points per operation
* Sprejemi (incoming shipments) — supplier quality
* Končni izdelki (finished goods) — final inspection

Features:
* Inspection checklists (boolean, numeric, pass/fail)
* Tolerance ranges (min/max acceptable values)
* Auto-trigger on stock move or production order
* Non-conformance reports (NC)
* Corrective actions (CAPA)
* Statistical Process Control (SPC) charts
* ISO 9001 / IATF 16949 audit trail
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['stock', 'mrp'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/l10n_si_quality_check_views.xml',
        'views/l10n_si_quality_nonconformance_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
