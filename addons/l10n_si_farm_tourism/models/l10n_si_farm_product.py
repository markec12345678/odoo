# -*- coding: utf-8 -*-
"""Domači izdelki - sir, mleko, jajca, meso, pršut, med, žganje."""
from odoo import fields, models


class L10nSiFarmProduct(models.Model):
    _name = 'l10n_si.farm.product'
    _description = 'Slovenian Farm Product'
    _order = 'category, name'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, size=16)
    product_id = fields.Many2one('product.product', required=True, ondelete='restrict')

    category = fields.Selection(
        selection=[('dairy', 'Mlečni izdelki'),
                   ('meat', 'Meso in mesni izdelki'),
                   ('eggs', 'Jajca'),
                   ('honey', 'Med'),
                   ('spirits', 'Žganje in likerji'),
                   ('wine', 'Vino'),
                   ('bakery', 'Pekovsko'),
                   ('produce', 'Zelenjava/sadje'),
                   ('crafts', 'Rokodelstvo'),
                   ('other', 'Drugo')],
        default='dairy',
        required=True,
    )

    # Certifications
    eko_certified = fields.Boolean(string='EKO (biološko)')
    eko_cert_body = fields.Selection(
        selection=[('biodar', 'Biodar'),
                   ('kontrakt', 'Kontrakt'),
                   ('icer', 'ICER'),
                   ('other', 'Drugo')],
        string='Certifikat',
    )
    slovenian_quality = fields.Boolean(
        string='Slovenska kvaliteta (kmetijski izdelek)',
        help='Certifikat "Izbrana kakovost - Slovenija".',
    )
    local_product = fields.Boolean(string='Lokalni izdelek', default=True)

    # Production
    production_method = fields.Selection(
        selection=[('homemade', 'Domača proizvodnja'),
                   ('bought', 'Kupljeno za nadaljnjo prodajo'),
                   ('processed', 'Predelano na kmetiji')],
        default='homemade',
    )
    quantity_in_stock = fields.Float(string='Na zalogi', default=0.0)
    unit = fields.Selection(
        selection=[('kg', 'kg'),
                   ('l', 'l'),
                   ('piece', 'kos'),
                   ('dozen', 'voken'),
                   ('package', 'paket')],
        default='kg',
    )

    # Pricing
    price_per_unit = fields.Float(related='product_id.lst_price', store=False)
    tax_rate = fields.Selection(
        selection=[('22', '22% (splošno)'),
                   ('9.5', '9.5% (živila)'),
                   ('5', '5% (knjige/časopisi)'),
                   ('0', '0% (oproščeno)')],
        default='9.5',
        help='Davčna stopnja za prodajo.',
    )

    # Sale location
    sold_on_farm = fields.Boolean(string='Prodaja na kmetiji', default=True)
    sold_online = fields.Boolean(string='Spletna prodaja', default=False)
    sold_at_market = fields.Boolean(string='Sejemski oder', default=False)

    active = fields.Boolean(default=True)
    image = fields.Binary()
    description = fields.Text()
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 'Code must be unique per company.'),
    ]
