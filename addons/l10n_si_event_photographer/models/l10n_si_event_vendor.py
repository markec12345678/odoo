# -*- coding: utf-8 -*-
"""Vendor - zunanji izvajalec (fotograf, DJ, cvetličar, ...)."""
from odoo import fields, models


class L10nSiEventVendor(models.Model):
    _name = 'l10n_si.event.vendor'
    _description = 'Slovenian Event Vendor'
    _inherit = ['mail.thread']
    _order = 'category, name'

    name = fields.Char(required=True, translate=True, tracking=True)
    active = fields.Boolean(default=True)
    partner_id = fields.Many2one('res.partner', required=True, ondelete='restrict')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    category = fields.Selection(
        selection=[('photographer', 'Fotograf'),
                   ('videographer', 'Videoproducent'),
                   ('dj', 'DJ'),
                   ('band', 'Glasbena skupina'),
                   ('florist', 'Cvetličar'),
                   ('decorator', 'Dekorater'),
                   ('mc', 'Vodja prireditve (MC)'),
                   ('transport', 'Prevoz (limuzina)'),
                   ('cake', 'Pek/Poročna torta'),
                   ('other', 'Drugo')],
        default='photographer',
        required=True,
    )

    # Storitve in cene
    services_description = fields.Text(string='Storitve')
    base_price = fields.Float(string='Osnovna cena (EUR)', default=500.0)
    hourly_rate = fields.Float(string='Cena na uro (EUR)', default=50.0)
    package_deal = fields.Boolean(string='Stranka paket', default=True)

    # Kontakt
    contact_name = fields.Char(related='partner_id.name', store=False)
    contact_phone = fields.Char(related='partner_id.phone', store=False)
    contact_email = fields.Char(related='partner_id.email', store=False)
    website = fields.Char(related='partner_id.website', store=False)

    # Spletna prisotnost
    portfolio_url = fields.Char(string='Portfolio URL')
    instagram = fields.Char()
    facebook = fields.Char()

    # Ocenjevanje
    rating = fields.Selection(
        selection=[('0', 'Brez ocene'),
                   ('1', '1 - Slab'),
                   ('2', '2 - Srednji'),
                   ('3', '3 - Dober'),
                   ('4', '4 - Zelo dober'),
                   ('5', '5 - Odličen')],
        default='3',
        tracking=True,
    )
    notes = fields.Text(string='Izkušnje sodelovanja')

    # Zgodovina
    booking_ids = fields.One2many('l10n_si.event.vendor.booking', 'vendor_id', string='Naročila')
    booking_count = fields.Integer(compute='_compute_count', store=False)

    def _compute_count(self):
        for v in self:
            v.booking_count = len(v.booking_ids)
