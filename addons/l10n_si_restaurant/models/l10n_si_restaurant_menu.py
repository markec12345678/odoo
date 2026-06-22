# -*- coding: utf-8 -*-
"""Jedilnik - menu items with allergens and daily specials."""
from odoo import api, fields, models


class L10nSiRestaurantMenu(models.Model):
    _name = 'l10n_si.restaurant.menu'
    _description = 'Slovenian Restaurant Menu Item'
    _order = 'category_id, sequence, name'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    product_id = fields.Many2one(
        'product.product', required=True, ondelete='restrict',
        help='Product used for invoicing. Tax + price from product.',
    )

    category_id = fields.Many2one('l10n_si.restaurant.menu.category', string='Kategorija')
    description = fields.Text(translate=True)
    image = fields.Binary()

    # Pricing
    price = fields.Float(related='product_id.lst_price', store=False)
    daily_special = fields.Boolean(string='Dnevna ponudba', default=False)
    valid_from = fields.Date(string='Velja od')
    valid_to = fields.Date(string='Velja do')

    # Allergens (EU 1169/2011 — 14 mandatory allergens)
    allergen_gluten = fields.Boolean(string='Gluten')
    allergen_crustaceans = fields.Boolean(string='Raki')
    allergen_eggs = fields.Boolean(string='Jajca')
    allergen_fish = fields.Boolean(string='Ribe')
    allergen_peanuts = fields.Boolean(string='Arašidi')
    allergen_soy = fields.Boolean(string='Soja')
    allergen_milk = fields.Boolean(string='Mleko')
    allergen_nuts = fields.Boolean(string='Oreški')
    allergen_celery = fields.Boolean(string='Zelena')
    allergen_mustard = fields.Boolean(string='Gorčica')
    allergen_sesame = fields.Boolean(string='Sezam')
    allergen_sulphites = fields.Boolean(string='Sulfiti')
    allergen_lupin = fields.Boolean(string='Volčji bob')
    allergen_molluscs = fields.Boolean(string='Mehkužci')

    # Dietary
    vegetarian = fields.Boolean(default=False)
    vegan = fields.Boolean(default=False)
    contains_pork = fields.Boolean(default=False, help='Za muslimanske/židovske goste')

    # Kitchen
    prep_time_minutes = fields.Integer(string='Priprava (min)', default=15)
    station = fields.Selection(
        selection=[('cold', 'Hladna kuhinja'),
                   ('grill', 'Žar'),
                   ('fryer', 'Friteza'),
                   ('oven', 'Pečica'),
                   ('bar', 'Bar')],
        default='cold',
    )

    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.name
            self.price = self.product_id.lst_price


class L10nSiRestaurantMenuCategory(models.Model):
    _name = 'l10n_si.restaurant.menu.category'
    _description = 'Slovenian Restaurant Menu Category'
    _order = 'sequence, name'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    code = fields.Char(required=True, size=8)
    active = fields.Boolean(default=True)
    item_count = fields.Integer(compute='_compute_count', store=False)

    def _compute_count(self):
        for cat in self:
            cat.item_count = self.env['l10n_si.restaurant.menu'].search_count([
                ('category_id', '=', cat.id),
                ('active', '=', True),
            ])
