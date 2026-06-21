# -*- coding: utf-8 -*-
"""WhatsApp message — sent or received."""
import logging

import requests

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class L10nSiWhatsappMessage(models.Model):
    _name = 'l10n_si.whatsapp.message'
    _description = 'Slovenian WhatsApp Message'
    _inherit = ['mail.thread']
    _order = 'create_date DESC'

    partner_id = fields.Many2one('res.partner', required=True, ondelete='cascade')
    phone = fields.Char(required=True, help='E.164 format: 38631123456 (no +)')
    direction = fields.Selection(
        selection=[('outgoing', 'Odhodno'),
                   ('incoming', 'Dohodno')],
        required=True,
        default='outgoing',
    )
    body = fields.Text(required=True)
    template_id = fields.Many2one('l10n_si.whatsapp.template', string='Used template')

    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('queued', 'V čakalni vrsti'),
                   ('sent', 'Poslano'),
                   ('delivered', 'Dostavljeno'),
                   ('read', 'Prebrano'),
                   ('failed', 'Neuspešno'),
                   ('received', 'Prejeto')],
        default='draft',
        tracking=True,
    )
    message_id = fields.Char(readonly=True, copy=False, help='WhatsApp message ID')
    error_message = fields.Text(readonly=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    # Linked record (for context)
    res_model = fields.Char(string='Linked model')
    res_id = fields.Integer(string='Linked ID')

    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    def action_send(self):
        """Send the message via the configured backend."""
        for msg in self:
            if not msg.partner_id.si_whatsapp_opt_in:
                msg.write({
                    'state': 'failed',
                    'error_message': _('Partner has not opted in for WhatsApp.'),
                })
                continue
            try:
                if msg.company_id.si_whatsapp_backend == 'cloud_api':
                    msg._send_cloud_api()
                elif msg.company_id.si_whatsapp_backend == 'twilio':
                    msg._send_twilio()
            except Exception as e:  # noqa: BLE001
                msg.write({'state': 'failed', 'error_message': str(e)})

    def _send_cloud_api(self):
        """Send via WhatsApp Cloud API."""
        self.ensure_one()
        company = self.company_id
        url = f'https://graph.facebook.com/v18.0/{company.si_whatsapp_phone_number_id}/messages'
        payload = {
            'messaging_product': 'whatsapp',
            'to': self.phone,
            'type': 'text',
            'text': {'body': self.body},
        }
        response = requests.post(
            url,
            headers={
                'Authorization': f'Bearer {company.si_whatsapp_access_token}',
                'Content-Type': 'application/json',
            },
            json=payload,
            timeout=15,
        )
        if response.status_code == 200:
            data = response.json()
            self.write({
                'state': 'sent',
                'message_id': data.get('messages', [{}])[0].get('id', ''),
            })
        else:
            self.write({
                'state': 'failed',
                'error_message': f'HTTP {response.status_code}: {response.text}',
            })

    def _send_twilio(self):
        """Send via Twilio WhatsApp API."""
        self.ensure_one()
        company = self.company_id
        url = f'https://api.twilio.com/2010-04-01/Accounts/{company.si_whatsapp_twilio_account_sid}/Messages.json'
        response = requests.post(
            url,
            auth=(company.si_whatsapp_twilio_account_sid, company.si_whatsapp_twilio_auth_token),
            data={
                'From': f'whatsapp:{company.si_whatsapp_twilio_from}',
                'To': f'whatsapp:+{self.phone}',
                'Body': self.body,
            },
            timeout=15,
        )
        if response.status_code in (200, 201):
            data = response.json()
            self.write({
                'state': 'sent',
                'message_id': data.get('sid', ''),
            })
        else:
            self.write({
                'state': 'failed',
                'error_message': f'HTTP {response.status_code}: {response.text}',
            })

    @api.model
    def receive_incoming(self, payload):
        """Process an incoming webhook payload from WhatsApp Cloud API."""
        try:
            for entry in payload.get('entry', []):
                for change in entry.get('changes', []):
                    value = change.get('value', {})
                    if 'messages' not in value:
                        continue
                    for msg_data in value['messages']:
                        phone = msg_data.get('from', '')
                        text = msg_data.get('text', {}).get('body', '')
                        partner = self.env['res.partner'].search([
                            '|', ('mobile', 'like', phone),
                            ('phone', 'like', phone),
                        ], limit=1)
                        self.create({
                            'partner_id': partner.id if partner else False,
                            'phone': phone,
                            'direction': 'incoming',
                            'body': text,
                            'state': 'received',
                            'message_id': msg_data.get('id', ''),
                        })
        except Exception as e:  # noqa: BLE001
            _logger.warning('WhatsApp incoming payload failed: %s', e)
