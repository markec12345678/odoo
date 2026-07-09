import logging
import requests
from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

WA_API_BASE = 'https://graph.facebook.com/v18.0'


class WhatsAppMessage(models.Model):
    _name = 'wa.message'
    _description = 'WhatsApp Message'
    _order = 'create_date DESC'

    name = fields.Char(string='Reference', readonly=True, copy=False, default='/')
    partner_id = fields.Many2one('res.partner', string='Recipient')
    phone = fields.Char(string='Phone Number', required=True, help='Format: 386XXXXXXXX (no +, no spaces)')
    message_body = fields.Text(string='Message', required=True)
    template_id = fields.Many2one('wa.template', string='Template Used')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('received', 'Received'),
    ], default='draft', tracking=True)
    wa_message_id = fields.Char(string='WhatsApp Message ID', readonly=True, copy=False)
    error_message = fields.Text(readonly=True, copy=False)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    direction = fields.Selection([('outgoing', 'Outgoing'), ('incoming', 'Incoming')], default='outgoing')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('wa.message') or '/'
        return super().create(vals_list)

    def action_send(self):
        """Send message via WhatsApp Cloud API."""
        self.ensure_one()
        company = self.company_id
        if not company.wa_enabled or not company.wa_phone_number_id or not company.wa_access_token:
            raise UserError(_('WhatsApp is not configured for company %s') % company.name)

        url = f"{WA_API_BASE}/{company.wa_phone_number_id}/messages"
        headers = {
            'Authorization': f'Bearer {company.wa_access_token}',
            'Content-Type': 'application/json',
        }
        payload = {
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': self.phone,
            'type': 'text',
            'text': {'body': self.message_body},
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                self.write({
                    'state': 'sent',
                    'wa_message_id': data.get('messages', [{}])[0].get('id', ''),
                })
                return True
            else:
                error = response.text[:500]
                _logger.error('WhatsApp API error: %s', error)
                self.write({'state': 'failed', 'error_message': error})
                return False
        except Exception as e:
            _logger.error('WhatsApp send error: %s', e)
            self.write({'state': 'failed', 'error_message': str(e)})
            return False

    def action_send_template(self):
        """Send a template message."""
        self.ensure_one()
        if not self.template_id:
            raise UserError(_('No template selected.'))
        company = self.company_id
        url = f"{WA_API_BASE}/{company.wa_phone_number_id}/messages"
        headers = {
            'Authorization': f'Bearer {company.wa_access_token}',
            'Content-Type': 'application/json',
        }
        payload = {
            'messaging_product': 'whatsapp',
            'to': self.phone,
            'type': 'template',
            'template': {
                'name': self.template_id.name,
                'language': {'code': self.template_id.language or 'sl'},
            },
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                self.write({
                    'state': 'sent',
                    'wa_message_id': data.get('messages', [{}])[0].get('id', ''),
                })
            else:
                self.write({'state': 'failed', 'error_message': response.text[:500]})
        except Exception as e:
            self.write({'state': 'failed', 'error_message': str(e)})
