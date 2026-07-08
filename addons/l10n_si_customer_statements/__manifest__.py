# -*- coding: utf-8 -*-
{
    'name': 'Slovenian Customer Statements',
    'summary': 'Monthly customer account statements with open invoices + aging',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Localizations',
    'description': """
Slovenian Customer Statements
==============================

Generate and send monthly customer statements (izpisi stanj kupcev) with:
* Open invoices (issued + unreconciled)
* Payments received in period
* Aging buckets (0-30, 31-60, 61-90, 90+ days)
* PDF attachment emailed to customer
* Multi-currency
* Optional: payment reminder (opomin) per ZVPot

Replaces Enterprise `account_customer_statements`.
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': ['account', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/l10n_si_customer_statement_views.xml',
        'wizard/l10n_si_customer_statement_wizard_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'countries': ['si'],
    'qweb': [
        'reports/l10n_si_customer_statement_report.xml',
    ],
}