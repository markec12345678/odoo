# -*- coding: utf-8 -*-
"""Website booking engine controller."""
import json
import logging
from datetime import datetime, timedelta

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class L10nSiWebsiteBooking(http.Controller):
    """Public booking engine - no auth required for search."""

    @http.route('/book', type='http', auth='public', website=True)
    def booking_search(self, **kwargs):
        """Search page - guest enters dates and sees availability."""
        check_in = kwargs.get('check_in')
        check_out = kwargs.get('check_out')
        adults = int(kwargs.get('adults', 2))
        children = int(kwargs.get('children', 0))

        room_types = []
        if check_in and check_out:
            try:
                ci_date = datetime.strptime(check_in, '%Y-%m-%d').date()
                co_date = datetime.strptime(check_out, '%Y-%m-%d').date()
                nights = (co_date - ci_date).days
                if nights > 0:
                    room_types = request.env['l10n_si.hotel.room.type'].sudo().search([
                        ('active', '=', True),
                    ])
                    # Compute rate for each room type
                    for rt in room_types:
                        rate_plan = request.env['l10n_si.rate.plan'].sudo().search([
                            ('hotel_room_type_id', '=', rt.id),
                            ('active', '=', True),
                        ], limit=1)
                        if rate_plan:
                            rt.computed_rate = rate_plan.get_rate_for_date(ci_date) * nights
                        else:
                            rt.computed_rate = rt.list_price * nights
                        rt.nights = nights
                        # Check availability
                        rt.available_rooms = request.env['l10n_si.hotel.room'].sudo().search_count([
                            ('room_type_id', '=', rt.id),
                            ('state', '=', 'available'),
                            ('active', '=', True),
                        ])
            except (ValueError, TypeError):
                pass

        return request.render('l10n_si_website_booking.booking_search_page', {
            'room_types': room_types,
            'check_in': check_in,
            'check_out': check_out,
            'adults': adults,
            'children': children,
        })

    @http.route('/book/checkout', type='http', auth='public', website=True, methods=['POST'])
    def booking_checkout(self, **kwargs):
        """Checkout page - guest enters personal details + payment."""
        room_type_id = kwargs.get('room_type_id')
        check_in = kwargs.get('check_in')
        check_out = kwargs.get('check_out')
        adults = kwargs.get('adults', 2)
        children = kwargs.get('children', 0)
        promo_code = kwargs.get('promo_code', '').strip().upper()

        room_type = request.env['l10n_si.hotel.room.type'].sudo().browse(int(room_type_id)) if room_type_id else False
        if not room_type or not check_in or not check_out:
            return request.redirect('/book')

        ci_date = datetime.strptime(check_in, '%Y-%m-%d').date()
        co_date = datetime.strptime(check_out, '%Y-%m-%d').date()
        nights = (co_date - ci_date).days

        # Get rate
        rate_plan = request.env['l10n_si.rate.plan'].sudo().search([
            ('hotel_room_type_id', '=', room_type.id),
            ('active', '=', True),
        ], limit=1)
        base_amount = rate_plan.get_rate_for_date(ci_date) * nights if rate_plan else room_type.list_price * nights

        # Apply promo
        discount_amount = 0.0
        promo = False
        if promo_code:
            promo = request.env['l10n_si.booking.promo'].sudo().search([
                ('code', '=', promo_code),
                ('active', '=', True),
            ], limit=1)
            if promo:
                valid, msg = promo.is_valid(ci_date, co_date, room_type.id)
                if valid:
                    discount_amount = promo.apply_discount(base_amount)
                else:
                    promo = False  # invalid

        total_amount = base_amount - discount_amount
        return request.render('l10n_si_website_booking.booking_checkout_page', {
            'room_type': room_type,
            'check_in': check_in,
            'check_out': check_out,
            'nights': nights,
            'adults': adults,
            'children': children,
            'base_amount': base_amount,
            'discount_amount': discount_amount,
            'total_amount': total_amount,
            'promo_code': promo_code,
            'promo_valid': bool(promo),
        })

    @http.route('/book/confirm', type='http', auth='public', website=True, methods=['POST'])
    def booking_confirm(self, **kwargs):
        """Confirm booking - create reservation + partner."""
        try:
            room_type_id = int(kwargs.get('room_type_id'))
            check_in = kwargs.get('check_in')
            check_out = kwargs.get('check_out')
            adults = int(kwargs.get('adults', 2))
            guest_name = kwargs.get('guest_name', '').strip()
            guest_email = kwargs.get('guest_email', '').strip()
            guest_phone = kwargs.get('guest_phone', '').strip()
            total_amount = float(kwargs.get('total_amount', 0))

            if not guest_name or not guest_email:
                return request.render('l10n_si_website_booking.booking_error', {
                    'error': 'Ime in e-pošta sta obvezna.',
                })

            ci_date = datetime.strptime(check_in, '%Y-%m-%d')
            co_date = datetime.strptime(check_out, '%Y-%m-%d')

            # Find or create partner
            partner = request.env['res.partner'].sudo().search([
                ('email', '=', guest_email),
            ], limit=1)
            if not partner:
                partner = request.env['res.partner'].sudo().create({
                    'name': guest_name,
                    'email': guest_email,
                    'phone': guest_phone,
                })

            # Find available room of this type
            room = request.env['l10n_si.hotel.room'].sudo().search([
                ('room_type_id', '=', room_type_id),
                ('state', '=', 'available'),
                ('active', '=', True),
            ], limit=1)
            if not room:
                return request.render('l10n_si_website_booking.booking_error', {
                    'error': 'Na žalost ni več prostih sob tega tipa.',
                })

            # Create reservation
            reservation = request.env['l10n_si.hotel.reservation'].sudo().create({
                'partner_id': partner.id,
                'room_id': room.id,
                'check_in': ci_date,
                'check_out': co_date,
                'adults': adults,
                'source': 'website',
                'daily_rate': total_amount / max((co_date - ci_date).days, 1),
            })
            reservation.action_confirm()

            return request.render('l10n_si_website_booking.booking_success', {
                'reservation': reservation,
                'guest_name': guest_name,
                'total_amount': total_amount,
            })
        except Exception as e:
            _logger.exception('Booking confirm error: %s', e)
            return request.render('l10n_si_website_booking.booking_error', {
                'error': str(e),
            })

    @http.route('/book/validate_promo', type='json', auth='public', methods=['POST'])
    def validate_promo(self, **kwargs):
        """AJAX endpoint to validate promo code in real-time."""
        data = request.get_json_data()
        promo_code = (data.get('promo_code') or '').strip().upper()
        check_in = data.get('check_in')
        check_out = data.get('check_out')

        if not promo_code:
            return json.dumps({'valid': False, 'message': 'Vnesite kodo.'})

        promo = request.env['l10n_si.booking.promo'].sudo().search([
            ('code', '=', promo_code),
            ('active', '=', True),
        ], limit=1)
        if not promo:
            return json.dumps({'valid': False, 'message': 'Koda ne obstaja.'})

        ci = datetime.strptime(check_in, '%Y-%m-%d').date() if check_in else False
        co = datetime.strptime(check_out, '%Y-%m-%d').date() if check_out else False
        valid, msg = promo.is_valid(ci, co)
        return json.dumps({'valid': valid, 'message': msg, 'discount_type': promo.discount_type, 'discount_value': promo.discount_value})
