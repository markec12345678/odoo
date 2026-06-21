# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Subscription Management (Advanced)',
    'summary': 'Recurring billing: SaaS, memberships, leases — replaces Enterprise sale_subscription',
    'version': '19.0.1.0.0',
    'category': 'Sales/Subscriptions',
    'description': """
Slovenian Subscription Management
=================================

Recurring billing for:
* SaaS subscriptions (monthly/annual)
* Memberships (članarine)
* Equipment leases (najemnine)
* Service contracts (vzdrževalne pogodbe)

Features:
* Recurring invoice generation (cron monthly/quarterly/annual)
* Tiered pricing plans
* Auto-renew vs fixed-term
* Trial periods
* Upgrades/downgrades with prorated invoicing
* Customer portal: see + manage subscriptions
* Cancellation workflows
* Linked to FURS e-Račun (via l10n_si_edi)
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['account', 'sale_management', 'mail', 'portal'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/l10n_si_subscription_plan_views.xml',
        'views/l10n_si_subscription_views.xml',
        'reports/l10n_si_subscription_report.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
