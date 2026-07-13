# -*- coding: utf-8 -*-
"""Procurement item - katalog artiklov za nabavo."""
from odoo import fields, models


class L10nSiProcurementItem(models.Model):
    _name = 'l10n_si.procurement.item'
    _description = 'Slovenian Procurement Item'
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
        selection=[('cleaning_supplies', 'Čistila'),
                   ('cosmetics', 'Kozmetika'),
                   ('linen', 'Posteljnina'),
                   ('food_meat', 'Hrana - meso'),
                   ('food_dairy', 'Hrana - mlečno'),
                   ('food_vegetables', 'Hrana - zelenjava'),
                   ('food_dry', 'Hrana - suho'),
                   ('beverages_alcohol', 'Pijača - alkohol'),
                   ('beverages_non_alcohol', 'Pijača - brez alkohola'),
                   ('office', 'Pisarniški material'),
                   ('technical', 'Tehnična oprema'),
                   ('other', 'Drugo')],
        default='cleaning_supplies',
        required=True,
    )

    # Enota
    uom = fields.Selection(
        selection=[('kg', 'kg'),
                   ('l', 'l'),
                   ('piece', 'kos'),
                   ('package', 'paket'),
                   ('box', 'škatla'),
                   ('dozen', 'voken')],
        default='piece',
        required=True,
    )

    # Inventory
    min_stock = fields.Float(required=True, default=10.0, string='Min. zaloga')
    max_stock = fields.Float(default=100.0, string='Max. zaloga')
    reorder_qty = fields.Float(default=50.0, string='Naročilna količina')

    # Pogostost naročanja
    order_frequency = fields.Selection(
        selection=[('daily', 'Dnevno'),
                   ('weekly', 'Tedensko'),
                   ('monthly', 'Mesečno'),
                   ('quarterly', 'Kvartalno'),
                   ('on_demand', 'Na zahtevo')],
        default='weekly',
        required=True,
    )

    # Sezonskost
    seasonal_demand = fields.Boolean(default=False, string='Sezonska potražnja')
    summer_multiplier = fields.Float(default=1.0, string='Poletni faktor')
    winter_multiplier = fields.Float(default=1.0, string='Zimski faktor')

    # Hranjenje
    storage_location = fields.Char(string='Lokacija skladiščenja')
    requires_cold_chain = fields.Boolean(default=False, string='Hladna veriga')
    expiry_days = fields.Integer(default=0, string='Rok uporabe (dnevi)')

    description = fields.Text()
    image = fields.Binary()

    # Povezave
    preferred_vendor_id = fields.Many2one('l10n_si.procurement.vendor', string='Prednostni dobavitelj')
    contract_id = fields.Many2one('l10n_si.procurement.contract', string='Aktivna pogodba')

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 'Code must be unique per company.'),
    ]

    def action_create_purchase_order(self):
        """Ustvari purchase order za ta artikel."""
        self.ensure_one()
        if not self.preferred_vendor_id:
            return False
        Po = self.env['purchase.order']
        po = Po.create({
            'partner_id': self.preferred_vendor_id.partner_id.id,
            'order_line': [(0, 0, {
                'product_id': self.product_id.id,
                'name': self.name,
                'product_qty': self.reorder_qty,
                'product_uom': self.env.ref('uom.product_uom_unit').id,
                'price_unit': self.preferred_vendor_id.unit_price,
            })],
        })
        return po
