# -*- coding: utf-8 -*-
"""Partner portal — guest self check-in, reservations, upsell."""
import logging

from odoo import http, _
from odoo.http import request

_logger = logging.getLogger(__name__)


class L10nSiPartnerPortal(http.Controller):

    @http.route('/my/stays', type='http', auth='user', website=True)
    def my_stays(self, **kw):
        folios = request.env['l10n_si.hotel.folio'].sudo().search([
            ('partner_id', '=', request.env.user.partner_id.id)
        ])
        return request.render('l10n_si_partner_portal.portal_stays', {'folios': folios})

    @http.route('/my/loyalty', type='http', auth='user', website=True)
    def my_loyalty(self, **kw):
        member = request.env['l10n_si.loyalty.member'].sudo().search([
            ('partner_id', '=', request.env.user.partner_id.id)
        ], limit=1)
        return request.render('l10n_si_partner_portal.portal_loyalty', {'member': member})

    # ====================================================================
    # SELF CHECK-IN
    # ====================================================================

    @http.route('/my/checkin/<int:folio_id>', type='http', auth='user', website=True)
    def self_checkin(self, folio_id, **kw):
        """Self check-in form — guest fills personal data before arrival."""
        folio = request.env['l10n_si.hotel.folio'].sudo().browse(folio_id)
        if not folio.exists() or folio.partner_id != request.env.user.partner_id:
            return request.not_found()

        # Check if already checked in
        existing_reg = request.env.get('l10n_si.etourism.guest.registration')
        already_registered = False
        if existing_reg:
            already_registered = existing_reg.sudo().search([
                ('partner_id', '=', folio.partner_id.id),
                ('arrival_date', '>=', folio.check_in),
            ], limit=1)

        countries = request.env['res.country'].sudo().search([])
        return request.render('l10n_si_partner_portal.self_checkin', {
            'folio': folio,
            'countries': countries,
            'already_registered': already_registered,
        })

    @http.route('/my/checkin/<int:folio_id>/submit', type='http', auth='user', website=True)
    def self_checkin_submit(self, folio_id, **kw):
        """Process self check-in form — create eTurizem registration."""
        folio = request.env['l10n_si.hotel.folio'].sudo().browse(folio_id)
        if not folio.exists() or folio.partner_id != request.env.user.partner_id:
            return request.not_found()

        # Extract form data
        first_name = kw.get('first_name', '').strip()
        last_name = kw.get('last_name', '').strip()
        birth_date = kw.get('birth_date', '')
        sex = kw.get('sex', '')
        citizenship = kw.get('citizenship', '')
        doc_type = kw.get('document_type', 'osebna_izkaznica')
        doc_number = kw.get('document_number', '').strip()
        doc_country = kw.get('document_country', '')
        address = kw.get('address', '').strip()
        purpose = kw.get('purpose', 'leisure')

        # Validate required fields
        if not first_name or not last_name or not doc_number:
            return request.render('l10n_si_partner_portal.self_checkin_error', {
                'folio': folio,
                'error': _('Ime, priimek in številka dokumenta so obvezni.'),
            })

        # Get country records
        citizenship_country = request.env['res.country'].sudo().browse(int(citizenship)) if citizenship else False
        doc_country_rec = request.env['res.country'].sudo().browse(int(doc_country)) if doc_country else False

        # Create eTurizem registration if module is installed
        Registration = request.env.get('l10n_si.etourism.guest.registration')
        registration = False
        if Registration:
            try:
                vals = {
                    'partner_id': folio.partner_id.id,
                    'guest_first_name': first_name,
                    'guest_last_name': last_name,
                    'guest_birth_date': birth_date or False,
                    'guest_sex': sex if sex in ('M', 'F', 'X') else False,
                    'guest_citizenship_id': citizenship_country.id if citizenship_country else False,
                    'guest_birth_country_id': citizenship_country.id if citizenship_country else False,
                    'guest_document_type': doc_type,
                    'guest_document_number': doc_number,
                    'guest_document_country_id': doc_country_rec.id if doc_country_rec else False,
                    'guest_address': address,
                    'arrival_date': folio.check_in,
                    'departure_date': folio.check_out,
                    'purpose': purpose,
                }
                # Add establishment if available
                est = getattr(folio.company_id, 'l10n_si_etourism_establishment_id', False)
                if est:
                    vals['establishment_id'] = est.id

                registration = Registration.sudo().create(vals)
                _logger.info('Self check-in: registration %s created for %s %s',
                             registration.id, first_name, last_name)
            except Exception as e:
                _logger.error('Self check-in: registration failed: %s', e)

        # Update partner record
        folio.partner_id.sudo().write({
            'firstname': first_name,
            'lastname': last_name,
            'name': f'{first_name} {last_name}',
        })

        return request.render('l10n_si_partner_portal.self_checkin_success', {
            'folio': folio,
            'registration': registration,
            'first_name': first_name,
        })

    # ====================================================================
    # UPSELL PAGE
    # ====================================================================

    @http.route('/my/upsell/<int:folio_id>', type='http', auth='user', website=True)
    def upsell_page(self, folio_id, **kw):
        """Upsell page — offer additional services during check-in."""
        folio = request.env['l10n_si.hotel.folio'].sudo().browse(folio_id)
        if not folio.exists() or folio.partner_id != request.env.user.partner_id:
            return request.not_found()

        # Get available services
        services = []
        # Late checkout
        services.append({
            'name': _('Pozna odjava (do 14:00)'),
            'description': _('Ostanite dlje brez naglice. Check-out do 14:00 namesto 11:00.'),
            'price': 20.00,
            'icon': '🕐',
        })
        # Airport transfer
        services.append({
            'name': _('Prevoz z letališča'),
            'description': _('Privatni prevoz z letališča do hotela. Udobno in brez stresa.'),
            'price': 35.00,
            'icon': '✈️',
        })
        # Breakfast
        services.append({
            'name': _('Zajtrk (dodatni)'),
            'description': _('Bogat samopostrežni zajtrk z lokalnimi specialitetami.'),
            'price': 12.00,
            'icon': '🥐',
        })
        # Wellness
        services.append({
            'name': _('Wellness paket'),
            'description': _('Dostop do savne, bazena in masaže (30 min).'),
            'price': 45.00,
            'icon': '💆',
        })

        return request.render('l10n_si_partner_portal.upsell_page', {
            'folio': folio,
            'services': services,
        })

    # ====================================================================
    # DIGITAL WELCOME GUIDE
    # ====================================================================

    @http.route('/my/guide/<int:folio_id>', type='http', auth='user', website=True)
    def digital_guide(self, folio_id, **kw):
        """Digital welcome guide — WiFi, house rules, local tips."""
        folio = request.env['l10n_si.hotel.folio'].sudo().browse(folio_id)
        if not folio.exists() or folio.partner_id != request.env.user.partner_id:
            return request.not_found()

        company = folio.company_id
        # Get WiFi info from company settings
        wifi_network = getattr(company, 'wa_business_phone', '') or 'Hotel_Guest_WiFi'
        wifi_password = 'Gost2025'

        guide_data = {
            'wifi_network': wifi_network,
            'wifi_password': wifi_password,
            'checkin_time': '14:00',
            'checkout_time': '11:00',
            'breakfast_time': '7:00 - 10:00',
            'wellness_hours': '9:00 - 21:00',
            'reception_phone': getattr(company, 'phone', '') or '+386 1 234 5678',
            'emergency': '112',
            'house_rules': [
                _('Tihanje od 22:00 do 7:00'),
                _('Kajenje prepovedano v sobah'),
                _('Hišne ljubljenčke najavite vnaprej'),
                _('Brisače iz soba ne odnašajte'),
            ],
            'local_tips': [
                {'name': _('Bled'), 'desc': _('15 min vožnja — jezero, otok, grad'), 'icon': '🏰'},
                {'name': _('Ljubljana'), 'desc': _('25 min vožnje — staro mestno jedro'), 'icon': '🏙️'},
                {'name': _('Vintgar'), 'desc': _('30 min — soteska z leseno potjo'), 'icon': '🌊'},
            ],
        }

        return request.render('l10n_si_partner_portal.digital_guide', {
            'folio': folio,
            'guide': guide_data,
        })
