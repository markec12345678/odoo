from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    wa_phone_number_id = fields.Char(string='WhatsApp Phone Number ID')
    wa_access_token = fields.Char(string='WhatsApp Access Token')
    wa_business_phone = fields.Char(string='WhatsApp Business Phone')
    wa_verify_token = fields.Char(string='Webhook Verify Token', default='si_hr_tourism_wa')
    wa_enabled = fields.Boolean(string='WhatsApp Enabled', default=False)
