# -*- coding: utf-8 -*-
"""WhatsApp Business konfiguracija na res.company."""
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    wa_phone_number_id = fields.Char(
        string='WhatsApp Phone Number ID',
        help='Phone Number ID iz Meta WhatsApp Business dashboard.',
    )
    wa_access_token = fields.Char(
        string='WhatsApp Access Token',
        help='Permanent access token iz Meta App dashboard.',
    )
    wa_business_phone = fields.Char(
        string='WhatsApp Business Phone',
        help='Številka v formatu 38641234567 (brez +).',
    )
    wa_verify_token = fields.Char(
        string='Webhook Verify Token',
        help='Token za verifikacijo webhook-a (poljuben niz).',
        default='si_hr_tourism_wa_verify',
    )
    wa_enabled = fields.Boolean(
        string='WhatsApp omogočen', default=False,
        help='Omogoči pošiljanje WhatsApp sporočil.',
    )
    wa_auto_reply = fields.Boolean(
        string='AI auto-odgovor', default=False,
        help='Ko je omogočeno, AI samodejno odgovori na vhodna WhatsApp '
             'sporočila gostov. Uporablja AI Core centralni router.',
    )
