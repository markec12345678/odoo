# -*- coding: utf-8 -*-
"""Procurement vendor - dobavitelj."""
from odoo import fields, models


class L10nSiProcurementVendor(models.Model):
    _name = 'l10n_si.procurement.vendor'
    _description = 'Slovenian Procurement Vendor'
    _inherit = ['mail.thread']
    _order = 'rating DESC, name'

    name = fields.Char(required=True, translate=True, tracking=True)
    active = fields.Boolean(default=True)
    partner_id = fields.Many2one('res.partner', required=True, ondelete='restrict')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # Kontakt
    contact_name = fields.Char(related='partner_id.name', store=False)
    contact_phone = fields.Char(related='partner_id.phone', store=False)
    contact_email = fields.Char(related='partner_id.email', store=False)

    # Kategorije, ki jih dobavitelj pokriva
    categories_supplied = fields.Char(string='Kategorije (CSV)',
                                        help='npr. "cleaning_supplies, food_dairy"')

    # Pogoji
    payment_terms = fields.Char(string='Plačilni pogoji', default='30 dni')
    delivery_time_days = fields.Integer(default=2, string='Doba dobave (dnevi)')
    min_order_value = fields.Float(default=0.0, string='Min. vrednost naročila (EUR)')
    free_delivery_threshold = fields.Float(default=500.0, string='Brezplačna dostava nad (EUR)')

    # Cena in popusti
    unit_price = fields.Float(default=0.0, string='Cena na enoto (EUR)')
    discount_percent = fields.Float(default=0.0, string='Standardni popust (%)')
    rebate_percent = fields.Float(default=0.0, string='Letni rebate (%)',
                                    help='Letni povratni popust glede na promet.')

    # Ocene
    rating = fields.Selection(
        selection=[('1', '1 - Nezanesljiv'),
                   ('2', '2 - Slab'),
                   ('3', '3 - Srednji'),
                   ('4', '4 - Dober'),
                   ('5', '5 - Odličen')],
        default='3',
        tracking=True,
    )

    # Status
    state = fields.Selection(
        selection=[('active', 'Aktiven'),
                   ('paused', 'Pavziran'),
                   ('blacklisted', 'Črni seznam')],
        default='active',
        tracking=True,
    )

    # Statistika
    contract_ids = fields.One2many('l10n_si.procurement.contract', 'vendor_id', string='Pogodbe')
    item_ids = fields.One2many('l10n_si.procurement.item', 'preferred_vendor_id', string='Artikli')

    notes = fields.Text(string='Izkušnje sodelovanja')

    def action_pause(self):
        self.write({'state': 'paused'})

    def action_blacklist(self):
        self.write({'state': 'blacklisted'})

    def action_activate(self):
        self.write({'state': 'active'})
