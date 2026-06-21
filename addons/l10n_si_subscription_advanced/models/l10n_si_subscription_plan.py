# -*- coding: utf-8 -*-
from odoo import fields, models


class L10nSiSubscriptionPlan(models.Model):
    """Pricing plan — defines what a subscription looks like."""
    _name = 'l10n_si.subscription.plan'
    _description = 'Slovenian Subscription Plan'
    _order = 'sequence, name'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    product_id = fields.Many2one(
        'product.product', string='Product', required=True,
        help='The product that will be invoiced on each renewal.',
    )
    description = fields.Text()

    # Pricing
    recurring_price = fields.Float(string='Cena (€)', required=True, default=0.0)
    recurring_interval = fields.Integer(
        string='Interval', required=True, default=1,
        help='Number of units between invoices (e.g. 1 month, 3 months).',
    )
    recurring_rule = fields.Selection(
        selection=[('daily', 'Dnevno'),
                   ('weekly', 'Tedensko'),
                   ('monthly', 'Mesečno'),
                   ('quarterly', 'Kvartalno'),
                   ('yearly', 'Letno')],
        default='monthly',
        required=True,
    )

    # Trial + commitment
    trial_period_days = fields.Integer(default=0, string='Trial obdobje (dnevi)')
    auto_renew = fields.Boolean(default=True, string='Avtomatska obnova')
    commitment_months = fields.Integer(
        default=0, string='Zavezujoča doba (mesecev)',
        help='Customer cannot cancel before N months. 0 = no commitment.',
    )

    # Currency + company
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id, required=True,
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )
