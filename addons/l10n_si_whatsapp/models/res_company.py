# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    si_whatsapp_backend = fields.Selection(
        selection=[('cloud_api', 'WhatsApp Cloud API (Meta)'),
                   ('twilio', 'Twilio WhatsApp')],
        default='cloud_api',
        required=True,
    )
    si_whatsapp_phone_number_id = fields.Char(string='Phone Number ID (Cloud API)')
    si_whatsapp_business_id = fields.Char(string='Business Account ID')
    si_whatsapp_access_token = fields.Char(string='Access Token')
    si_whatsapp_verify_token = fields.Char(
        string='Webhook Verify Token',
        help='Token for verifying the webhook URL when Meta subscribes.',
    )
    si_whatsapp_twilio_account_sid = fields.Char(string='Twilio Account SID')
    si_whatsapp_twilio_auth_token = fields.Char(string='Twilio Auth Token')
    si_whatsapp_twilio_from = fields.Char(string='Twilio from number')
