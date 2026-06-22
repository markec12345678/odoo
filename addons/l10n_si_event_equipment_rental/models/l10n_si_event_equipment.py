# -*- coding: utf-8 -*-
"""Equipment catalog with stock quantity."""
from odoo import api, fields, models


class L10nSiEventEquipment(models.Model):
    _name = 'l10n_si.event.equipment'
    _description = 'Slovenian Event Equipment'
    _order = 'category, name'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, size=16)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )
    product_id = fields.Many2one('product.product', required=True, ondelete='restrict')

    category = fields.Selection(
        selection=[('projector', 'Projektorji'),
                   ('screen', 'Platna'),
                   ('audio', 'Zvok (zvočniki, mešalke)'),
                   ('microphone', 'Mikrofoni'),
                   ('lighting', 'Razsvetljava'),
                   ('stage', 'Odri in scenska oprema'),
                   ('table', 'Mize'),
                   ('chair', 'Stoli'),
                   ('decoration', 'Dekoracije'),
                   ('other', 'Drugo')],
        default='projector',
        required=True,
    )

    # Stock
    quantity_total = fields.Integer(string='Skupno na zalogi', default=1, required=True)
    quantity_available = fields.Integer(
        compute='_compute_available', store=False,
        string='Trenutno prosto',
    )

    # Pricing
    hourly_rate = fields.Float(string='Cena/h (EUR)', default=10.0)
    daily_rate = fields.Float(string='Cena/dan (EUR)', default=50.0)
    deposit = fields.Float(string='Kaucija (EUR)', default=0.0)

    description = fields.Text()
    image = fields.Binary()

    rental_line_ids = fields.One2many(
        'l10n_si.event.equipment.rental.line', 'equipment_id', string='Najemi',
    )

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 'Code must be unique per company.'),
    ]

    def _compute_available(self):
        """Available = total - currently rented (overlapping with now)."""
        now = fields.Datetime.now()
        for eq in self:
            rented = self.env['l10n_si.event.equipment.rental.line'].search([
                ('equipment_id', '=', eq.id),
                ('rental_id.date_from', '<=', now),
                ('rental_id.date_to', '>=', now),
                ('rental_id.state', 'in', ['confirmed', 'in_progress']),
            ])
            rented_qty = sum(rented.mapped('quantity'))
            eq.quantity_available = eq.quantity_total - rented_qty

    def is_available(self, date_from, date_to, quantity=1, exclude_line_id=False):
        """Preveri, ali je na voljo dovolj količin v danem času."""
        self.ensure_one()
        domain = [
            ('equipment_id', '=', self.id),
            ('rental_id.date_from', '<', date_to),
            ('rental_id.date_to', '>', date_from),
            ('rental_id.state', 'in', ['confirmed', 'in_progress']),
        ]
        if exclude_line_id:
            domain.append(('id', '!=', exclude_line_id))
        rented = self.env['l10n_si.event.equipment.rental.line'].search(domain)
        rented_qty = sum(rented.mapped('quantity'))
        return (self.quantity_total - rented_qty) >= quantity
