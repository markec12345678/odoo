# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    si_hotel_default_checkin_time = fields.Float(
        string='Privzet čas prijave', default=14.0,
        help='14.0 = 14:00. Used for new reservations.',
    )
    si_hotel_default_checkout_time = fields.Float(
        string='Privzet čas odjave', default=10.0,
        help='10.0 = 10:00.',
    )
    si_hotel_breakfast_included = fields.Boolean(
        string='Zajtrk vključen v ceno', default=True,
    )
    si_hotel_tourist_tax_per_person = fields.Float(
        string='Turistična taksa (EUR/osebo/nočitev)',
        default=2.50,
        help='Pripravljena za povezavo z l10n_si_tourist_tax modulom.',
    )
