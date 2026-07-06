# -*- coding: utf-8 -*-
"""Public portal for guests to report issues (QR code in room → URL)."""
import base64
import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class L10nSiMaintenancePortal(http.Controller):
    """Guest-facing portal for reporting maintenance issues.

    Tipičen workflow:
    1. Gost skenira QR kodo v sobi
    2. Brskalnik odpre /maintenance/report/room/SI101
    3. Gost izpolni obrazec + naloži fotografijo
    4. Submit → maintenance request ustvarjen, recepcija obveščena
    """

    @http.route('/maintenance/report/room/<string:room_number>', type='http', auth='public', website=True)
    def report_form(self, room_number, **kwargs):
        """Prikaži obrazec za prijavo napake."""
        room = request.env['l10n_si.hotel.room'].sudo().search([
            ('number', '=', room_number),
        ], limit=1)
        if not room:
            return request.render('l10n_si_maintenance_request.portal_room_not_found', {'room_number': room_number})
        return request.render('l10n_si_maintenance_request.portal_report_form', {
            'room': room,
        })

    @http.route('/maintenance/submit', type='http', auth='public', methods=['POST'], website=True, csrf=True)
    def submit(self, **kwargs):
        """Submit forma - create maintenance request."""
        try:
            room_id = int(kwargs.get('room_id', 0))
            category = kwargs.get('category', 'other')
            priority = kwargs.get('priority', '1')
            description = kwargs.get('description', '').strip()
            guest_name = kwargs.get('guest_name', '').strip()
            guest_email = kwargs.get('guest_email', '').strip()

            if not description:
                return request.render('l10n_si_maintenance_request.portal_error', {
                    'error': 'Opis je obvezen.',
                })

            # Najdi ali ustvari partnerja
            partner = False
            if guest_email:
                partner = request.env['res.partner'].sudo().search([
                    ('email', '=', guest_email),
                ], limit=1)
                if not partner and guest_name:
                    partner = request.env['res.partner'].sudo().create({
                        'name': guest_name,
                        'email': guest_email,
                    })

            # Create request
            req = request.env['l10n_si.maintenance.request'].sudo().create({
                'name': f'Prijavil gost - soba {kwargs.get("room_number", "?")}',
                'partner_id': partner.id if partner else False,
                'source': 'guest_portal',
                'room_id': room_id,
                'category': category,
                'description': description,
                'priority': priority,
            })

            # Process uploaded photos
            for file_key in ['photo1', 'photo2', 'photo3']:
                upload = kwargs.get(file_key)
                if upload and hasattr(upload, 'read'):
                    image_data = base64.b64encode(upload.read())
                    request.env['l10n_si.maintenance.request.photo'].sudo().create({
                        'request_id': req.id,
                        'image': image_data,
                        'caption': 'Photo from guest',
                    })

            return request.render('l10n_si_maintenance_request.portal_success', {
                'request_number': req.number,
            })
        except Exception as e:
            _logger.exception('Maintenance portal submit error: %s', e)
            return request.render('l10n_si_maintenance_request.portal_error', {
                'error': str(e),
            })

    @http.route('/maintenance/status/<string:request_number>', type='http', auth='public', website=True)
    def status(self, request_number):
        """Gost preveri status svoje prijave."""
        req = request.env['l10n_si.maintenance.request'].sudo().search([
            ('number', '=', request_number),
        ], limit=1)
        if not req:
            return request.not_found()
        state_labels = dict(req._fields['state'].selection)
        return request.render('l10n_si_maintenance_request.portal_status', {
            'req': req,
            'state_label': state_labels.get(req.state, req.state),
        })
