# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Slovenian Invoice Numbering',
    'summary': 'Slovenian invoice sequences by poslovni prostor (BL1-2025-0001)',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Localizations',
    'description': """
Slovenian Invoice Numbering
============================

Implements invoice numbering compliant with ZDavPR-1 (Pravilnik o zaščitnih
oznakah računov) which requires:

* Each **poslovni prostor** (business premise) has its own unique sequence
* Each **elektronska naprava** (electronic device / cash register) within a
  poslovni prostor has its own sub-sequence
* Numbers must be **strictly increasing** and **without gaps**
* Format: <business_premise>-<device>-<year>-<sequence>
  Example: BL1-KASA1-2025-00001

This module:
    * Adds `l10n_si.business.premise` model (registered with FURS)
    * Adds `l10n_si.electronic.device` model (cash register / device)
    * Configures `ir.sequence` per premise+device+year
    * Overrides `account.move` `_compute_name()` to use the SI sequence
      for outgoing invoices
    * Provides a wizard to mass-create sequences for the next year

Configuration:
    * Accounting → Configuration → Slovenian → Business Premises
    * Each premise linked to a `res.company`
    * Sequences auto-renew on Jan 1st (cron)

References:
    * ZDavPR-1, Pravilnik o zaščitnih oznakah računov (UR. l. RS š. 89/16)
""",
    'author': 'markec12345678',
    'website': 'https://github.com/markec12345678/odoo',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'l10n_si',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/l10n_si_business_premise_views.xml',
        'views/l10n_si_electronic_device_views.xml',
        'views/account_move_views.xml',
        'views/res_company_views.xml',
        'data/ir_sequence_cron.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'countries': ['si'],
}
