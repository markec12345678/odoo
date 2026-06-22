# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Sustainability (Green Key)',
    'summary': 'Green Key, EKO certifikati, poraba energije/vode, CO2 odtis',
    'version': '19.0.1.0.0',
    'category': 'Sustainability',
    'description': "Trajnostni razvoj: Green Key certifikat, poraba energije/vode, CO2, odpadki.",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/sustainability_data.xml',
        'views/l10n_si_sustainability_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
