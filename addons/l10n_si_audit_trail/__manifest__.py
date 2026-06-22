# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Audit Trail',
    'summary': 'Sledenje sprememb občutljivih podatkov (cene, davki, partnerji)',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'description': "Audit trail for sensitive field changes.",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': ['security/ir.model.access.csv', 'data/l10n_si_audit_trail_data.xml', 'views/l10n_si_audit_trail_views.xml'],
    'installable': True, 'application': True, 'auto_install': False,
}
