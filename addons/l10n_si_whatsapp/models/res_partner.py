# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    si_whatsapp_opt_in = fields.Boolean(
        string='WhatsApp soglasje',
        default=False,
        help='GDPR: customer must opt in before receiving WhatsApp messages.',
    )
    si_whatsapp_opt_in_date = fields.Datetime(readonly=True, copy=False)
    si_whatsapp_opt_out_date = fields.Datetime(readonly=True, copy=False)

    def action_si_whatsapp_opt_in(self):
        for partner in self:
            partner.write({
                'si_whatsapp_opt_in': True,
                'si_whatsapp_opt_in_date': fields.Datetime.now(),
                'si_whatsapp_opt_out_date': False,
            })

    def action_si_whatsapp_opt_out(self):
        for partner in self:
            partner.write({
                'si_whatsapp_opt_in': False,
                'si_whatsapp_opt_out_date': fields.Datetime.now(),
            })
