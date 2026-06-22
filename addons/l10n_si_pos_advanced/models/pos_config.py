# -*- coding: utf-8 -*-
from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    si_fiscal_enabled = fields.Boolean(
        string='FURS davčno potrjevanje',
        default=True,
        help='Generiraj ZOI/EOR za vsak POS račun.',
    )
    si_default_business_premise_id = fields.Many2one(
        'l10n_si.business.premise', string='Privzeti poslovni prostor (FURS)',
    )
    si_default_device_id = fields.Many2one(
        'l10n_si.electronic.device', string='Privzeta elektronska naprava',
    )
    si_allow_room_charge = fields.Boolean(
        string='Dovoli plačilo na hotelski folio',
        default=False,
    )
    si_add_tourist_tax = fields.Boolean(
        string='Avtomatsko dodaj turistično takso',
        default=False,
    )
    si_municipality_id = fields.Many2one(
        'l10n_si.tourist.tax.municipality', string='Občina za turistično takso',
    )
    si_print_eor_on_receipt = fields.Boolean(
        string='Natisni EOR na računu', default=True,
    )
    si_print_qr_code = fields.Boolean(
        string='Natisni QR kodo', default=True,
    )
