# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    si_loyalty_member_id = fields.Many2one(
        'l10n_si.loyalty.member', string='Loyalty Membership', copy=False,
    )
    si_loyalty_points = fields.Integer(related='si_loyalty_member_id.points_balance', store=False)
    si_loyalty_tier = fields.Selection(related='si_loyalty_member_id.tier', store=False)
