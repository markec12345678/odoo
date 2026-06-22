# -*- coding: utf-8 -*-
"""Obcina - municipality with its own tourist tax rate."""
from odoo import api, fields, models


class L10nSiTouristTaxMunicipality(models.Model):
    """Slovenian municipality (občina) with its tourist tax rate.

    Each of the 212 Slovenian municipalities sets its own rate via
    občinski odlok. The rate typically ranges 1.00 - 2.50 EUR.
    """
    _name = 'l10n_si.tourist.tax.municipality'
    _description = 'Slovenian Tourist Tax Municipality'
    _order = 'name'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, size=8, help='SI municipality code')
    country_id = fields.Many2one('res.country', default=lambda self: self.env.ref('base.si'), required=True)

    # Rate (per person per night)
    rate_adult = fields.Float(string='Odrasli (EUR)', required=True, default=2.00)
    rate_youth = fields.Float(string='Mladina 7-18 (EUR)', required=True, default=1.00,
                              help='Reduced rate for youth aged 7-18.')
    rate_child = fields.Float(string='Otroke 0-7 (EUR)', required=True, default=0.00,
                              help='Children under 7 are free.')

    # Exemptions + caps
    max_chargeable_nights = fields.Integer(
        string='Max nočitev za obračun',
        default=7,
        help='Maximum number of nights charged per stay. Typical: 7.',
    )
    disabled_exempt = fields.Boolean(
        string='Invalidi oproščeni',
        default=True,
        help='Disabled persons (with valid card) are exempt.',
    )
    tour_leader_exempt = fields.Boolean(
        string='Vodniki oproščeni',
        default=True,
        help='One tour leader per 20 guests is exempt.',
    )

    # Validity
    valid_from = fields.Date(default=lambda self: fields.Date.today())
    valid_to = fields.Date()
    active = fields.Boolean(default=True)

    # Account for payment
    tax_account_id = fields.Many2one(
        'account.account', string='Konto za takso',
        help='Account where collected tax is posted.',
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    transaction_count = fields.Integer(compute='_compute_count', store=False)
    total_collected = fields.Monetary(compute='_compute_count', store=False, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')

    def _compute_count(self):
        Transaction = self.env['l10n_si.tourist.tax.transaction']
        for m in self:
            txs = Transaction.search([('municipality_id', '=', m.id)])
            m.transaction_count = len(txs)
            m.total_collected = sum(txs.mapped('tax_amount'))

    @api.model
    def get_rate_for_age(self, municipality_id, age):
        """Return the appropriate rate based on guest age."""
        m = self.browse(municipality_id)
        if not m:
            return 0.0
        if age < 7:
            return m.rate_child
        elif age < 18:
            return m.rate_youth
        else:
            return m.rate_adult
