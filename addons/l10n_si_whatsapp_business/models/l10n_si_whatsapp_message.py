# -*- coding: utf-8 -*-
"""WhatsApp message model — sledi poslanim in prejetim sporočilom."""
import json
import logging
import requests
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

WA_API_BASE = 'https://graph.facebook.com/v21.0'


class L10nSiWhatsAppMessage(models.Model):
    _name = 'l10n_si.whatsapp.message'
    _description = 'WhatsApp Business Message'
    _order = 'create_date DESC'

    partner_id = fields.Many2one('res.partner', string='Prejemnik', required=True)
    phone_number = fields.Char(related='partner_id.mobile', string='Telefon', readonly=True)
    direction = fields.Selection([
        ('outgoing', 'Poslano'),
        ('incoming', 'Prejeto'),
    ], required=True, default='outgoing')
    message_type = fields.Selection([
        ('text', 'Besedilo'),
        ('template', 'Predloga'),
    ], required=True, default='text')
    body = fields.Text(string='Vsebina', required=True)
    template_id = fields.Many2one('l10n_si.whatsapp.template', string='Predloga')
    state = fields.Selection([
        ('draft', 'Osnutek'),
        ('sent', 'Poslano'),
        ('delivered', 'Dostavljeno'),
        ('read', 'Prebrano'),
        ('failed', 'Neuspešno'),
    ], default='draft', tracking=True)
    wa_message_id = fields.Char(string='WhatsApp Message ID', readonly=True, copy=False)
    error_message = fields.Text(readonly=True, copy=False)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, required=True)

    def action_send(self):
        """Pošlji WhatsApp sporočilo preko Cloud API."""
        self.ensure_one()
        company = self.company_id
        if not company.wa_enabled:
            raise UserError(_('WhatsApp ni omogočen za to podjetje.'))
        if not company.wa_phone_number_id or not company.wa_access_token:
            raise UserError(_('Manjka WhatsApp Phone Number ID ali Access Token.'))
        
        phone = self.partner_id.mobile or self.partner_id.phone
        if not phone:
            raise UserError(_('Partner nima telefonske številke.'))
        # Odstrani presledke, +, če je
        phone = phone.replace(' ', '').replace('+', '').replace('-', '')
        
        if self.message_type == 'template' and self.template_id:
            payload = {
                'messaging_product': 'whatsapp',
                'to': phone,
                'type': 'template',
                'template': {
                    'name': self.template_id.name,
                    'language': {'code': self.template_id.language or 'sl'},
                }
            }
        else:
            payload = {
                'messaging_product': 'whatsapp',
                'to': phone,
                'type': 'text',
                'text': {'body': self.body},
            }
        
        url = f'{WA_API_BASE}/{company.wa_phone_number_id}/messages'
        headers = {
            'Authorization': f'Bearer {company.wa_access_token}',
            'Content-Type': 'application/json',
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                self.write({
                    'state': 'sent',
                    'wa_message_id': data.get('messages', [{}])[0].get('id', ''),
                })
                _logger.info('WhatsApp message sent to %s: %s', phone, self.wa_message_id)
            else:
                error = response.text[:500]
                self.write({'state': 'failed', 'error_message': error})
                _logger.error('WhatsApp send failed: %s', error)
        except Exception as e:
            self.write({'state': 'failed', 'error_message': str(e)[:500]})
            _logger.error('WhatsApp send error: %s', e)

    def action_send_reservation_confirmation(self, partner_id, reservation_data):
        """Pošlji potrditev rezervacije preko WhatsApp."""
        template = self.env.ref('l10n_si_whatsapp_business.template_reservation_confirm', raise_if_not_found=False)
        if template:
            msg = self.create({
                'partner_id': partner_id,
                'direction': 'outgoing',
                'message_type': 'template',
                'template_id': template.id,
                'body': f'Potrditev rezervacije: {reservation_data}',
            })
            msg.action_send()
            return msg
        return False

    @api.model
    def _cron_send_checkin_reminders(self):
        """Avtomatsko pošlji opomnik za check-in 24 ur pred prihodom.

        Isče potrdjene rezervacije s check-in datumom jutri in pošlje
        opomnik gostu preko WhatsAppa, če ima partner mobilni telefon.
        """
        tomorrow = fields.Date.to_string(fields.Date.today() + timedelta(days=1))
        # Poisci rezervacije s check-in jutri (model l10n_si.hotel.reservation)
        Reservation = self.env.get('l10n_si.hotel.reservation')
        if not Reservation:
            return
        reservations = Reservation.search([
            ('check_in', '>=', tomorrow + ' 00:00:00'),
            ('check_in', '<=', tomorrow + ' 23:59:59'),
            ('state', 'in', ['confirmed', 'checked_in']),
        ])
        template = self.env.ref('l10n_si_whatsapp_business.template_checkin_reminder', raise_if_not_found=False)
        if not template:
            return
        for res in reservations:
            partner = res.folio_id.partner_id if hasattr(res, 'folio_id') else res.partner_id
            if not partner or not (partner.mobile or partner.phone):
                continue
            # Preveri, ali smo že poslali opomnik za to rezervacijo
            existing = self.search([
                ('partner_id', '=', partner.id),
                ('template_id', '=', template.id),
                ('create_date', '>=', fields.Datetime.to_string(fields.Datetime.now() - timedelta(hours=24))),
            ], limit=1)
            if existing:
                continue
            company = res.company_id or self.env.company
            if not company.wa_enabled:
                continue
            msg = self.create({
                'partner_id': partner.id,
                'direction': 'outgoing',
                'message_type': 'template',
                'template_id': template.id,
                'body': f'Check-in opomnik: {res.name or ""}',
                'company_id': company.id,
            })
            msg.action_send()

    @api.model
    def _cron_send_checkout_reminders(self):
        """Avtomatsko pošlji opomnik za check-out na dan odhoda."""
        today = fields.Date.to_string(fields.Date.today())
        Reservation = self.env.get('l10n_si.hotel.reservation')
        if not Reservation:
            return
        reservations = Reservation.search([
            ('check_out', '>=', today + ' 00:00:00'),
            ('check_out', '<=', today + ' 23:59:59'),
            ('state', '=', 'checked_in'),
        ])
        template = self.env.ref('l10n_si_whatsapp_business.template_checkout_reminder', raise_if_not_found=False)
        if not template:
            return
        for res in reservations:
            partner = res.folio_id.partner_id if hasattr(res, 'folio_id') else res.partner_id
            if not partner or not (partner.mobile or partner.phone):
                continue
            existing = self.search([
                ('partner_id', '=', partner.id),
                ('template_id', '=', template.id),
                ('create_date', '>=', fields.Datetime.to_string(fields.Datetime.now() - timedelta(hours=12))),
            ], limit=1)
            if existing:
                continue
            company = res.company_id or self.env.company
            if not company.wa_enabled:
                continue
            msg = self.create({
                'partner_id': partner.id,
                'direction': 'outgoing',
                'message_type': 'template',
                'template_id': template.id,
                'body': f'Check-out opomnik: {res.name or ""}',
                'company_id': company.id,
            })
            msg.action_send()

    @api.model
    def _cron_send_feedback_requests(self):
        """Pošlji prošnjo za povratne informacije 2 uri po check-out."""
        two_hours_ago = fields.Datetime.to_string(fields.Datetime.now() - timedelta(hours=2))
        Reservation = self.env.get('l10n_si.hotel.reservation')
        if not Reservation:
            return
        reservations = Reservation.search([
            ('check_out', '<=', two_hours_ago),
            ('state', '=', 'done'),
        ])
        template = self.env.ref('l10n_si_whatsapp_business.template_feedback_request', raise_if_not_found=False)
        if not template:
            return
        for res in reservations:
            partner = res.folio_id.partner_id if hasattr(res, 'folio_id') else res.partner_id
            if not partner or not (partner.mobile or partner.phone):
                continue
            existing = self.search([
                ('partner_id', '=', partner.id),
                ('template_id', '=', template.id),
            ], limit=1)
            if existing:
                continue
            company = res.company_id or self.env.company
            if not company.wa_enabled:
                continue
            msg = self.create({
                'partner_id': partner.id,
                'direction': 'outgoing',
                'message_type': 'template',
                'template_id': template.id,
                'body': f'Prošnja za povratne informacije: {res.name or ""}',
                'company_id': company.id,
            })
            msg.action_send()
