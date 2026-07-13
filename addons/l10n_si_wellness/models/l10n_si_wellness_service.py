# -*- coding: utf-8 -*-
"""Wellness service - masaža, sauna, bazen, itd."""
from odoo import fields, models


class L10nSiWellnessService(models.Model):
    _name = 'l10n_si.wellness.service'
    _description = 'Slovenian Wellness Service'
    _order = 'category, name'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, size=16)
    active = fields.Boolean(default=True)
    product_id = fields.Many2one('product.product', required=True, ondelete='restrict')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    category = fields.Selection(
        selection=[('pool', 'Bazen'),
                   ('sauna', 'Sauna'),
                   ('massage', 'Masaža'),
                   ('beauty', 'Lepota'),
                   ('treatment', 'Zdravljenje'),
                   ('fitness', 'Fitnes'),
                   ('other', 'Drugo')],
        default='massage',
        required=True,
    )

    description = fields.Text()
    image = fields.Binary()

    # Trajanje in cena
    duration_minutes = fields.Integer(required=True, default=60)
    price_adult = fields.Float(required=True, default=40.0,
                                help='Cena za odrasle (EUR)')
    price_child = fields.Float(default=20.0, string='Cena otroci 7-15')
    price_senior = fields.Float(default=32.0, string='Cena seniorji 65+')
    price_student = fields.Float(default=36.0, string='Cena študenti')

    # Potreben maser/terapevt
    requires_therapist = fields.Boolean(default=True, string='Potreben terapevt')
    therapist_role = fields.Char(string='Vloga (npr. maser, kozmetik)')

    # Kapaciteta (za skupinske: npr. bazen)
    capacity = fields.Integer(default=1, help='Število hkratnih gostov')
    is_group_activity = fields.Boolean(string='Skupinska', default=False)

    # Lokacija
    location = fields.Char(string='Lokacija znotraj objekta')

    booking_ids = fields.One2many('l10n_si.wellness.booking', 'service_id', string='Rezervacije')
    booking_count_today = fields.Integer(compute='_compute_today_count', store=False)

    def _compute_today_count(self):
        today = fields.Date.today()
        for s in self:
            s.booking_count_today = self.env['l10n_si.wellness.booking'].search_count([
                ('service_id', '=', s.id),
                ('date', '>=', today.strftime('%Y-%m-%d 00:00:00')),
                ('date', '<=', today.strftime('%Y-%m-%d 23:59:59')),
                ('state', 'in', ['confirmed', 'in_progress']),
            ])

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 'Code must be unique per company.'),
    ]
