# -*- coding: utf-8 -*-
"""Catering menu items - jedi in pijače za dogodke."""
from odoo import fields, models


class L10nSiEventMenuItem(models.Model):
    """Jedi in pijače za catering.

    Razlikuje se od l10n_si_restaurant.menu - ta je za dogodke (bulk).
    """
    _name = 'l10n_si.event.menu.item'
    _description = 'Slovenian Event Menu Item'
    _order = 'category, sequence, name'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    code = fields.Char(required=True, size=16)
    active = fields.Boolean(default=True)
    product_id = fields.Many2one(
        'product.product', required=True, ondelete='restrict',
        help='Product used for invoicing.',
    )

    category = fields.Selection(
        selection=[('welcome_drink', 'Pozdravni toast'),
                   ('appetizer', 'Hladne predjedi'),
                   ('soup', 'Juhe'),
                   ('main_meat', 'Glavne jedi - meso'),
                   ('main_fish', 'Glavne jedi - ribe'),
                   ('main_veg', 'Glavne jedi - vegi'),
                   ('side_dish', 'Priloge'),
                   ('salad', 'Solate'),
                   ('dessert', 'Sladice'),
                   ('wedding_cake', 'Poročna torta'),
                   ('coffee', 'Kava in čaj'),
                   ('wine', 'Vina'),
                   ('beer', 'Piva'),
                   ('spirits', 'Žganje/likerji'),
                   ('soft_drinks', 'Brezaalkoholne pijače'),
                   ('other', 'Drugo')],
        default='main_meat',
        required=True,
    )

    # Cena
    price_per_person = fields.Float(string='Cena na osebo (EUR)',
                                     related='product_id.lst_price', store=False)
    price_per_unit = fields.Float(string='Cena na enoto (EUR)', default=0.0,
                                    help='Za torte, vina - cena na enoto, ne na osebo.')

    # Diet
    vegetarian = fields.Boolean(default=False)
    vegan = fields.Boolean(default=False)
    gluten_free = fields.Boolean(default=False)
    contains_pork = fields.Boolean(default=False)
    contains_allergens = fields.Char(string='Alergeni',
                                      help='Prosto besedilo - glavni alergeni.')

    description = fields.Text(translate=True)
    image = fields.Binary()

    # Za katere pakete ustreza
    suitable_for_wedding = fields.Boolean(string='Za poroke', default=True)
    suitable_for_conference = fields.Boolean(string='Za konference', default=False)
    suitable_for_gala = fields.Boolean(string='Za gala', default=True)

    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 'Menu item code must be unique per company.'),
    ]
