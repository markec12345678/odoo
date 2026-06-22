# -*- coding: utf-8 -*-
"""Hotel service - minibar, sobna storitev, pralnica, ..."""
from odoo import fields, models


class HotelService(models.Model):
    """Storitve, ki se zaračunajo na folio (minibar, masaža, pralnica, ...)."""
    _name = 'l10n_si.hotel.service'
    _description = 'Slovenian Hotel Service'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, size=16)
    product_id = fields.Many2one(
        'product.product', required=True, ondelete='restrict',
        help='Product used for invoicing. Tax + account from product.',
    )
    category = fields.Selection(
        selection=[('minibar', 'Minibar'),
                   ('room_service', 'Sobna storitev'),
                   ('laundry', 'Pralnica'),
                   ('spa', 'Wellness/Spa'),
                   ('breakfast', 'Zajtrk'),
                   ('other', 'Drugo')],
        default='other',
        required=True,
    )
    default_price = fields.Float(related='product_id.lst_price', store=False)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 'Code must be unique per company.'),
    ]
