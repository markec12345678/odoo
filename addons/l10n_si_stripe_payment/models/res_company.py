from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    si_stripe_deposit_mode = fields.Boolean(
        string='Stripe Hotel Deposit Mode',
        default=False,
        help='When enabled, Stripe payments use pre-authorization (hold) instead of immediate capture. '
             'Useful for hotel deposits — capture at check-out.',
    )
    si_stripe_deposit_percentage = fields.Float(
        string='Default Deposit Percentage',
        default=30.0,
        help='Default percentage of total booking to charge as deposit (0-100)',
    )
