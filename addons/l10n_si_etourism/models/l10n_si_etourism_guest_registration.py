# -*- coding: utf-8 -*-
"""Prijava in odjava gosta pri AJPES eTurizem."""
import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .ajpes_client import (
    AJPESClient, AJPESAuthError, AJPESValidationError,
    AJPESConnectionError, AJPESUnknownError,
    build_guest_book_xml,
)

_logger = logging.getLogger(__name__)


class L10nSiEtourismGuestRegistration(models.Model):
    _name = 'l10n_si.etourism.guest.registration'
    _description = 'Slovenian eTurizem Guest Registration'
    _inherit = ['mail.thread']
    _order = 'arrival_date DESC'

    name = fields.Char(copy=False, readonly=True, default='/')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    establishment_id = fields.Many2one('l10n_si.etourism.establishment', required=True, ondelete='restrict', tracking=True)
    mid = fields.Char(related='establishment_id.mid', store=True, readonly=True)
    sifnas = fields.Char(related='establishment_id.sifnas', store=True, readonly=True)

    partner_id = fields.Many2one('res.partner', string='Gost', required=True, tracking=True)
    guest_first_name = fields.Char(string='Ime', required=True)
    guest_last_name = fields.Char(string='Priimek', required=True)
    guest_birth_date = fields.Date(string='Datum rojstva')
    guest_sex = fields.Selection(selection=[('M', 'Moški'), ('F', 'Ženska'), ('X', 'Drugo')], string='Spol')
    guest_citizenship_id = fields.Many2one('res.country', string='Državljanstvo')
    guest_birth_country_id = fields.Many2one('res.country', string='Država rojstva')
    guest_document_type = fields.Selection(
        selection=[('potni_list', 'Potni list'), ('osebna_izkaznica', 'Osebna izkaznica'),
                   ('vozni_list', 'Vozni list'), ('drugo', 'Drugo')],
        string='Vrsta dokumenta', required=True, default='osebna_izkaznica',
    )
    guest_document_number = fields.Char(string='Številka dokumenta', required=True)
    guest_document_country_id = fields.Many2one('res.country', string='Država izdajatelja dokumenta')
    guest_address = fields.Char(string='Stalni naslov gosta')

    arrival_date = fields.Datetime(string='Datum in ura prihoda', required=True, default=fields.Datetime.now)
    departure_date = fields.Datetime(string='Datum in ura odhoda')
    nights = fields.Integer(compute='_compute_nights', store=True, string='Nočitve')
    purpose = fields.Selection(
        selection=[('leisure', 'Prosti čas / dopust'), ('business', 'Poslovno'),
                   ('congress', 'Kongres / sejem'), ('medical', 'Zdravilišče / medicinsko'),
                   ('transit', 'Tranzit (< 24h)'), ('other', 'Drugo')],
        string='Namen bivanja', default='leisure', required=True,
    )
    transport = fields.Selection(
        selection=[('air', 'Letalo'), ('train', 'Vlak'), ('bus', 'Avtobus'),
                   ('car', 'Osebno vozilo'), ('ship', 'Ladja'), ('other', 'Drugo')],
        string='Vrsta prometa', default='car',
    )
    country_of_origin_id = fields.Many2one('res.country', string='Država prihoda')
    reservation_source = fields.Selection(
        selection=[('direct', 'Direktno'), ('agency', 'Agencija'), ('booking_com', 'Booking.com'),
                   ('airbnb', 'Airbnb'), ('expedia', 'Expedia'), ('other', 'Drugo')],
        string='Vir rezervacije', default='direct',
    )

    res_model = fields.Char(string='Izvirni dokument')
    res_id = fields.Integer(string='ID dokumenta')
    hotel_reservation_id = fields.Many2one('l10n_si.hotel.reservation', string='Hotelska rezervacija')
    hotel_folio_id = fields.Many2one('l10n_si.hotel.folio', string='Folio')
    camping_reservation_id = fields.Many2one('l10n_si.camping.reservation', string='Kamp rezervacija')

    ajpes_status = fields.Selection(
        selection=[('draft', 'Osnutek'), ('pending', 'V obdelavi'), ('submitted', 'Prijavljeno'),
                   ('deregistered', 'Odjavljeno'), ('error', 'Napaka'), ('cancelled', 'Preklicano')],
        string='AJPES status', default='draft', tracking=True, required=True,
    )
    ajpes_submission_id = fields.Char(string='AJPES številka potrdila', readonly=True, copy=False)
    ajpes_submitted_at = fields.Datetime(readonly=True, copy=False)
    ajpes_deregistered_at = fields.Datetime(readonly=True, copy=False)
    ajpes_error_message = fields.Text(readonly=True, copy=False)
    next_retry = fields.Datetime(readonly=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('l10n_si.etourism.guest.registration') or '/'
        return super().create(vals_list)

    @api.depends('arrival_date', 'departure_date')
    def _compute_nights(self):
        for reg in self:
            if reg.arrival_date and reg.departure_date:
                delta = reg.departure_date - reg.arrival_date
                reg.nights = max(delta.days, 0)
            else:
                reg.nights = 0

    def action_submit_to_ajpes(self):
        for reg in self:
            if reg.ajpes_status in ('submitted', 'deregistered'):
                continue
            reg._ajpes_register()

    def action_deregister_with_ajpes(self):
        for reg in self:
            if reg.ajpes_status != 'submitted':
                raise UserError(_('Cannot deregister — status is %s') % reg.ajpes_status)
            if not reg.departure_date:
                raise UserError(_('Departure date is required for deregistration.'))
            reg._ajpes_deregister()

    def action_cancel(self):
        self.write({'ajpes_status': 'cancelled'})

    def action_reset_to_draft(self):
        self.write({'ajpes_status': 'draft', 'ajpes_error_message': False, 'next_retry': False})

    def _ajpes_register(self):
        self.ensure_one()
        establishment = self.establishment_id
        if not establishment.si_pass_username and not establishment.si_pass_password:
            self.write({'ajpes_status': 'error', 'ajpes_error_message': _('No SI-PASS credentials configured.')})
            return False
        guest_book_xml = build_guest_book_xml(self)
        log_vals = {'registration_id': self.id, 'company_id': self.company_id.id,
                    'request_type': 'registration', 'request_xml': guest_book_xml, 'state': 'draft'}
        client = AJPESClient(
            username=establishment.si_pass_username,
            password=establishment.si_pass_password,
            environment=establishment.environment,
        )
        try:
            receipt_id, raw_response = client.submit_guest_book(guest_book_xml)
            self.write({'ajpes_status': 'submitted', 'ajpes_submission_id': receipt_id or self.name,
                        'ajpes_submitted_at': fields.Datetime.now(), 'ajpes_error_message': False, 'next_retry': False})
            log_vals.update({'state': 'sent', 'response_xml': raw_response, 'http_status': 200})
            self.env['l10n_si.etourism.log'].create(log_vals)
            return True
        except AJPESAuthError as e:
            self.write({'ajpes_status': 'error', 'ajpes_error_message': str(e), 'next_retry': False})
            log_vals.update({'state': 'error', 'error_message': str(e)})
            self.env['l10n_si.etourism.log'].create(log_vals)
            return False
        except AJPESValidationError as e:
            self.write({'ajpes_status': 'error', 'ajpes_error_message': str(e), 'next_retry': False})
            log_vals.update({'state': 'error', 'error_message': str(e)})
            self.env['l10n_si.etourism.log'].create(log_vals)
            return False
        except AJPESConnectionError as e:
            self.write({'ajpes_status': 'pending', 'ajpes_error_message': str(e), 'next_retry': fields.Datetime.now() + timedelta(minutes=15)})
            log_vals.update({'state': 'error', 'error_message': str(e)})
            self.env['l10n_si.etourism.log'].create(log_vals)
            return False
        except (AJPESUnknownError, Exception) as e:
            self.write({'ajpes_status': 'error', 'ajpes_error_message': str(e), 'next_retry': fields.Datetime.now() + timedelta(minutes=15)})
            log_vals.update({'state': 'error', 'error_message': str(e)})
            self.env['l10n_si.etourism.log'].create(log_vals)
            return False

    def _ajpes_deregister(self):
        self.ensure_one()
        if not self.ajpes_submission_id:
            self.write({'ajpes_status': 'error', 'ajpes_error_message': _('Cannot deregister — no prior submission_id.')})
            return False
        guest_book_xml = build_guest_book_xml(self)
        log_vals = {'registration_id': self.id, 'company_id': self.company_id.id,
                    'request_type': 'deregistration', 'request_xml': guest_book_xml, 'state': 'draft'}
        establishment = self.establishment_id
        client = AJPESClient(
            username=establishment.si_pass_username,
            password=establishment.si_pass_password,
            environment=establishment.environment,
        )
        try:
            receipt_id, raw_response = client.submit_guest_book(guest_book_xml)
            self.write({'ajpes_status': 'deregistered', 'ajpes_deregistered_at': fields.Datetime.now()})
            log_vals.update({'state': 'sent', 'response_xml': raw_response, 'http_status': 200})
            self.env['l10n_si.etourism.log'].create(log_vals)
            return True
        except (AJPESAuthError, AJPESValidationError) as e:
            self.write({'ajpes_status': 'error', 'ajpes_error_message': str(e)})
            log_vals.update({'state': 'error', 'error_message': str(e)})
            self.env['l10n_si.etourism.log'].create(log_vals)
            return False
        except (AJPESConnectionError, AJPESUnknownError, Exception) as e:
            self.write({'ajpes_status': 'error', 'ajpes_error_message': str(e), 'next_retry': fields.Datetime.now() + timedelta(minutes=15)})
            log_vals.update({'state': 'error', 'error_message': str(e)})
            self.env['l10n_si.etourism.log'].create(log_vals)
            return False

    @api.model
    def _cron_process_pending(self):
        pending = self.search([('ajpes_status', '=', 'pending'), ('next_retry', '<=', fields.Datetime.now())])
        for reg in pending:
            try:
                reg._ajpes_register()
            except Exception:
                _logger.exception('Cron failed for %s', reg.name)
