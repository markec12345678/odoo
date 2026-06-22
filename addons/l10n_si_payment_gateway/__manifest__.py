# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Payment Gateway',
    'summary': 'SI plačilni procesorji - Activa, Stripe, PayPal, UPN, TRR',
    'version': '19.0.1.0.0',
    'category': 'Accounting',
    'description': """
Slovenian Payment Gateway
=========================

Plačilni procesorji za slovenski trg:
* Activa Pay (slovenski procesor)
* Stripe (mednarodni)
* PayPal (mednarodni)
* UPN (Univerzalni Plačilni Nalog - SEPA)
* TRR (bančno nakazilo - avtomatsko usklajevanje z l10n_si_bank_parser)
* Gotovina (ročno)
* Darilni vavčer

Features:
* Več plačilnih metod naenkrat
* Avtomatsko usklajevanje plačil z računi
* 3D Secure (Strong Customer Authentication - SCA)
* Refund workflow
* Plačilni linki (URL pošlješ stranki)
* Recurring plačila (naročnine)
* Multi-currency
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['account', 'payment'],
    'data': [
        'security/ir.model.access.csv',
        'data/payment_data.xml',
        'views/l10n_si_payment_config_views.xml',
        'views/l10n_si_payment_transaction_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
