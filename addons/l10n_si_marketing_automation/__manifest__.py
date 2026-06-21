# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Marketing Automation',
    'summary': 'Multi-step email campaigns with branching + triggers — replaces Enterprise marketing_automation',
    'version': '19.0.1.0.0',
    'category': 'Marketing/Automation',
    'description': """
Slovenian Marketing Automation
===============================

Multi-step email campaigns with conditional branching.

Features:
* Triggers: signup, abandoned cart, birthday, custom event
* Steps: send email, wait N days, branch on condition, add tag
* Conditions: country, last purchase date, total spent, custom fields
* A/B testing of subject lines
* Open / click / bounce tracking
* Unsubscribe per campaign
* GDPR-compliant: consent tracking

Replaces Enterprise `marketing_automation`.
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['mail', 'mass_mailing'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/l10n_si_marketing_campaign_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
