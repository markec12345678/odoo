# -*- coding: utf-8 -*-
"""Croatian eVisitor guest registration (prijava gosta).

Lifecycle:
    draft → pending → submitted → deregistered
                       ↓
                      error  (retryable only on connection error)

* **draft**       — created, not yet sent
* **pending**     — queued for submission (auto-cron will pick it up)
* **submitted**   — successfully registered, ``evisitor_submission_id`` set
* **deregistered**— successfully checked-out
* **error**       — last submission failed; retried by cron only when the
                    failure was a connection error
"""
import json
import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .evisitor_client import (
    EVisitorAuthError,
    EVisitorConnectionError,
    EVisitorError,
    EVisitorUnknownError,
    EVisitorValidationError,
    build_check_in_payload,
    build_check_out_payload,
)

_logger = logging.getLogger(__name__)

# Retry interval for transient (connection) failures, in minutes.
RETRY_INTERVAL_MINUTES = 15
# Max retry attempts before giving up and surfacing the error permanently.
MAX_RETRIES = 8


class L10nHrEvisitorGuestRegistration(models.Model):
    _name = 'l10n_hr.evisitor.guest.registration'
    _description = 'Croatian eVisitor Guest Registration (Prijava gosta)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'arrival_date DESC, id DESC'

    name = fields.Char(
        string='Oznaka', required=True, copy=False, readonly=True,
        default=lambda self: _('Nova'),
    )
    company_id = fields.Many2one(
        'res.company', string='Tvrtka',
        default=lambda self: self.env.company, required=True,
    )
    accommodation_id = fields.Many2one(
        'l10n_hr.evisitor.accommodation', string='Smještaj', required=True,
        tracking=True, ondelete='restrict',
    )

    # ---- Guest (gost) -----------------------------------------------------
    first_name = fields.Char(string='Ime', required=True, tracking=True)
    last_name = fields.Char(string='Prezime', required=True, tracking=True)
    birth_date = fields.Date(string='Datum rođenja', tracking=True)
    sex = fields.Selection(
        selection=[('male', 'Muško'),
                   ('female', 'Žensko'),
                   ('other', 'Ostalo')],
        string='Spol', tracking=True,
    )
    citizenship_id = fields.Many2one(
        'res.country', string='Državljanstvo',
        default=lambda self: self.env.ref('base.hr').id, required=True,
    )
    citizenship_code = fields.Char(
        string='Državljanstvo (ISO)', compute='_compute_citizenship_code',
        store=True, readonly=True,
    )

    # ---- Travel document (putni dokument) ---------------------------------
    document_type = fields.Selection(
        selection=[('passport', 'Putovnica'),
                   ('id_card', 'Osobna iskaznica'),
                   ('drivers_license', 'Vozačka dozvola'),
                   ('other', 'Ostalo')],
        string='Tip dokumenta', required=True, default='passport', tracking=True,
    )
    document_number = fields.Char(
        string='Broj dokumenta', required=True, tracking=True,
    )
    document_country_id = fields.Many2one(
        'res.country', string='Država izdavanja dokumenta',
        default=lambda self: self.env.ref('base.hr').id, required=True,
    )
    document_country_code = fields.Char(
        string='Država dokumenta (ISO)', compute='_compute_document_country_code',
        store=True, readonly=True,
    )

    # ---- Address (adresa) -------------------------------------------------
    address_street = fields.Char(string='Ulica i broj')
    address_zip = fields.Char(string='Poštanski broj')
    address_city = fields.Char(string='Naselje')
    address_country_id = fields.Many2one(
        'res.country', string='Država adrese',
        default=lambda self: self.env.ref('base.hr').id,
    )
    address_country_code = fields.Char(
        string='Država adrese (ISO)', compute='_compute_address_country_code',
        store=True, readonly=True,
    )

    # ---- Stay (boravak) ---------------------------------------------------
    arrival_date = fields.Date(
        string='Datum dolaska', required=True, tracking=True,
    )
    departure_date = fields.Date(
        string='Datum odlaska (planirani)', required=True, tracking=True,
    )
    actual_departure_date = fields.Date(
        string='Stvarni datum odlaska', tracking=True,
        help='Koristi se pri odjavi (CheckOut); ako nije naveden, koristi se '
             'planirani datum odlaska.',
    )
    nights = fields.Integer(
        string='Broj noćenja', compute='_compute_nights', store=True,
    )
    purpose = fields.Selection(
        selection=[('tourist', 'Turistički'),
                   ('business', 'Poslovni'),
                   ('private', 'Privatni'),
                   ('other', 'Ostalo')],
        string='Svrha boravka', default='tourist', tracking=True,
    )
    transport = fields.Selection(
        selection=[('air', 'Zrakoplov'),
                   ('sea', 'Brod'),
                   ('road', 'Cestovni'),
                   ('rail', 'Željeznica'),
                   ('other', 'Ostalo')],
        string='Vrsta prijevoza', default='other', tracking=True,
    )
    country_of_origin_id = fields.Many2one(
        'res.country', string='Zemlja porijekla',
        default=lambda self: self.env.ref('base.hr').id, required=True,
    )
    country_of_origin_code = fields.Char(
        string='Zemlja porijekla (ISO)', compute='_compute_country_of_origin_code',
        store=True, readonly=True,
    )
    reservation_source = fields.Selection(
        selection=[('direct', 'Izravna rezervacija'),
                   ('agency', 'Turistička agencija'),
                   ('booking', 'Booking platforma'),
                   ('airbnb', 'Airbnb'),
                   ('other', 'Ostalo')],
        string='Izvor rezervacije', default='direct', tracking=True,
    )

    # ---- Occupancy (popunjenost) -----------------------------------------
    adults = fields.Integer(string='Broj odraslih', default=1, required=True)
    children = fields.Integer(string='Broj djece (0–11,99 g.)', default=0)
    youth = fields.Integer(string='Broj mladih (12–17,99 g.)', default=0)

    # ---- Tourist tax (boravišna pristojba) -------------------------------
    tourist_tax_amount = fields.Float(
        string='Boravišna pristojba (EUR)', compute='_compute_tourist_tax_amount',
        store=True, digits=(10, 2),
        help='Izračunato lokalno na temelju konfiguriranih stopa po smještaju. '
             'Stvarni iznos potvrđuje API prilikom prijave.',
    )

    # ---- eVisitor integration --------------------------------------------
    evisitor_status = fields.Selection(
        selection=[('draft', 'Nacrt'),
                   ('pending', 'Na čekanju'),
                   ('submitted', 'Prijavljeno'),
                   ('deregistered', 'Odjavljeno'),
                   ('error', 'Greška')],
        string='Status eVisitor', default='draft', required=True, tracking=True,
        copy=False,
    )
    evisitor_submission_id = fields.Char(
        string='eVisitor checkInId', readonly=True, copy=False,
        help='Jedinstveni identifikator prijave u sustavu eVisitor '
             '(vraća API nakon uspješnog CheckIn-a).',
    )
    evisitor_submitted_at = fields.Datetime(
        string='Vrijeme prijave', readonly=True, copy=False,
    )
    evisitor_deregistered_at = fields.Datetime(
        string='Vrijeme odjave', readonly=True, copy=False,
    )
    last_error = fields.Text(string='Posljednja greška', readonly=True, copy=False)
    next_retry = fields.Datetime(
        string='Sljedeći pokušaj', readonly=True, copy=False,
    )
    retry_count = fields.Integer(
        string='Broj pokušaja', default=0, readonly=True, copy=False,
    )
    log_ids = fields.One2many(
        'l10n_hr.evisitor.log', 'registration_id',
        string='Dnevnik eVisitor', readonly=True,
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_company_uniq', 'unique(name, company_id)',
         'Oznaka prijave mora biti jedinstvena po tvrtki.'),
    ]

    # ---------------------------------------------------------------------
    # Computes
    # ---------------------------------------------------------------------

    @api.depends('citizenship_id')
    def _compute_citizenship_code(self):
        for r in self:
            r.citizenship_code = r.citizenship_id.code or None

    @api.depends('document_country_id')
    def _compute_document_country_code(self):
        for r in self:
            r.document_country_code = r.document_country_id.code or None

    @api.depends('address_country_id')
    def _compute_address_country_code(self):
        for r in self:
            r.address_country_code = r.address_country_id.code or None

    @api.depends('country_of_origin_id')
    def _compute_country_of_origin_code(self):
        for r in self:
            r.country_of_origin_code = r.country_of_origin_id.code or None

    @api.depends('arrival_date', 'departure_date')
    def _compute_nights(self):
        for r in self:
            if r.arrival_date and r.departure_date and r.departure_date >= r.arrival_date:
                r.nights = (r.departure_date - r.arrival_date).days
            else:
                r.nights = 0

    @api.depends('accommodation_id', 'nights', 'adults', 'children', 'youth')
    def _compute_tourist_tax_amount(self):
        """Local tourist-tax estimate based on per-accommodation rates.

        The authoritative figure is returned by the API at CheckIn time;
        this field is an estimate so the user can preview the expected cost.
        Children under 12 are statutorily exempt in most municipalities —
        reflected by the default ``tourist_tax_child`` of 0.00.
        """
        for r in self:
            acc = r.accommodation_id
            if not acc or not r.nights:
                r.tourist_tax_amount = 0.0
                continue
            amount = (
                r.nights * (
                    r.adults * acc.tourist_tax_adult
                    + r.youth * acc.tourist_tax_youth
                    + r.children * acc.tourist_tax_child
                )
            )
            r.tourist_tax_amount = round(amount or 0.0, 2)

    # ---------------------------------------------------------------------
    # CRUD
    # ---------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _('Nova'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'l10n_hr.evisitor.guest.registration') or _('EVT/??????')
        return super().create(vals_list)

    @api.constrains('arrival_date', 'departure_date')
    def _check_dates(self):
        for r in self:
            if r.arrival_date and r.departure_date and r.departure_date < r.arrival_date:
                raise UserError(_(
                    'Datum odlaska ne može biti prije datuma dolaska.'))

    @api.constrains('adults', 'children', 'youth')
    def _check_occupancy(self):
        for r in self:
            for field_name in ('adults', 'children', 'youth'):
                if getattr(r, field_name) < 0:
                    raise UserError(_(
                        'Broj osoba ne može biti negativan (polje: %s).',
                        field_name))
            if r.adults + r.children + r.youth < 1:
                raise UserError(_('Broj osoba mora biti najmanje 1.'))

    # ---------------------------------------------------------------------
    # Public actions
    # ---------------------------------------------------------------------

    def action_submit_to_evisitor(self):
        """Manualna akcija: pošalji prijavu (CheckIn) u eVisitor."""
        for reg in self:
            if reg.evisitor_status in ('submitted', 'deregistered'):
                continue
            reg._evisitor_register()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Prijava poslana'),
                'message': _('Zahtjev za prijavu je obrađen.'),
                'type': 'info',
                'sticky': False,
            },
        }

    def action_deregister_with_evisitor(self):
        """Manualna akcija: odjavi gosta (CheckOut) u eVisitor."""
        for reg in self:
            if reg.evisitor_status != 'submitted':
                raise UserError(_(
                    'Samo prijave sa statusom „Prijavljeno” mogu biti odjavljene '
                    '(prijava %s ima status %s).',
                    reg.name, reg.evisitor_status))
            reg._evisitor_deregister()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Odjava poslana'),
                'message': _('Zahtjev za odjavu je obrađen.'),
                'type': 'info',
                'sticky': False,
            },
        }

    def action_reset_to_draft(self):
        """Vrati prijavu u nacrt (samo ako je u statusu greške)."""
        for reg in self:
            if reg.evisitor_status != 'error':
                raise UserError(_(
                    'Samo prijave u statusu „Greška” mogu biti vraćene u nacrt.'))
            reg.write({
                'evisitor_status': 'draft',
                'last_error': False,
                'next_retry': False,
                'retry_count': 0,
            })

    def action_view_logs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Dnevnik eVisitor'),
            'res_model': 'l10n_hr.evisitor.log',
            'view_mode': 'list,form',
            'domain': [('registration_id', '=', self.id)],
        }

    # ---------------------------------------------------------------------
    # eVisitor API calls
    # ---------------------------------------------------------------------

    def _get_evisitor_client(self):
        """Construct an EVisitorClient from the linked accommodation."""
        from .evisitor_client import EVisitorClient
        self.ensure_one()
        acc = self.accommodation_id
        if not acc.evisitor_username or not acc.evisitor_password:
            raise UserError(_(
                'Smještaj %s nema konfigurirano eVisitor korisničko ime/lozinku.',
                acc.display_name))
        # Company-level override of environment, if set.
        company = self.company_id or self.env.company
        environment = company.l10n_hr_evisitor_environment or acc.environment
        return EVisitorClient(
            username=acc.evisitor_username,
            password=acc.evisitor_password,
            environment=environment,
        )

    def _evisitor_register(self):
        """Pošalji CheckIn zahtjev u eVisitor i pohrani checkInId.

        Mapping grešaka:
        - AuthError / ValidationError / UnknownError → status „error”, bez retry-a
        - ConnectionError → status „pending”, zakazan retry za 15 minuta
        """
        Log = self.env['l10n_hr.evisitor.log']
        for reg in self:
            acc = reg.accommodation_id
            try:
                client = reg._get_evisitor_client()
            except UserError as e:
                reg._log_failure(
                    request_type='check_in',
                    error_message=str(e),
                    retryable=False,
                    request_payload=None,
                )
                reg.write({
                    'evisitor_status': 'error',
                    'last_error': str(e),
                })
                continue

            payload = build_check_in_payload(reg)
            log_vals = reg._prepare_log_vals(
                request_type='check_in', payload=payload)
            log = Log.create(log_vals)

            try:
                response = client.check_in(payload)
            except EVisitorAuthError as e:
                reg._handle_failure(log, str(e), retryable=False)
                continue
            except EVisitorValidationError as e:
                reg._handle_failure(log, str(e), retryable=False)
                continue
            except EVisitorConnectionError as e:
                reg._handle_failure(log, str(e), retryable=True)
                continue
            except (EVisitorUnknownError, EVisitorError) as e:
                reg._handle_failure(log, str(e), retryable=False)
                continue

            check_in_id = (
                response.get('checkInId')
                or response.get('CheckInId')
                or response.get('id')
                if isinstance(response, dict) else None
            )
            if not check_in_id:
                # API responded 2xx but no checkInId — treat as unknown error.
                msg = _('API je odgovorio bez checkInId: %s') % (
                    json.dumps(response)[:500] if response else '<empty>')
                reg._handle_failure(
                    log, msg, retryable=False,
                    response_payload=json.dumps(response) if response else None,
                )
                continue

            log.write({
                'state': 'sent',
                'http_status': 200,
                'response_payload': json.dumps(response, default=str),
                'evisitor_submission_id': check_in_id,
            })
            reg.write({
                'evisitor_status': 'submitted',
                'evisitor_submission_id': check_in_id,
                'evisitor_submitted_at': fields.Datetime.now(),
                'last_error': False,
                'next_retry': False,
            })
            reg.message_post(body=_(
                'Gost prijavljen u eVisitor (checkInId: %s, boravišna '
                'pristojba ≈ %.2f EUR).', check_in_id, reg.tourist_tax_amount))

    def _evisitor_deregister(self):
        """Pošalji CheckOut zahtjev u eVisitor."""
        Log = self.env['l10n_hr.evisitor.log']
        for reg in self:
            if not reg.evisitor_submission_id:
                reg.message_post(body=_(
                    'Odjava nije moguća: prijava nema eVisitor checkInId.'))
                continue
            try:
                client = reg._get_evisitor_client()
            except UserError as e:
                reg._log_failure(
                    request_type='check_out',
                    error_message=str(e),
                    retryable=False,
                    request_payload=None,
                )
                continue

            payload = build_check_out_payload(reg)
            log_vals = reg._prepare_log_vals(
                request_type='check_out', payload=payload)
            log = Log.create(log_vals)

            try:
                response = client.check_out(payload)
            except EVisitorAuthError as e:
                reg._handle_failure(log, str(e), retryable=False)
                continue
            except EVisitorValidationError as e:
                reg._handle_failure(log, str(e), retryable=False)
                continue
            except EVisitorConnectionError as e:
                reg._handle_failure(log, str(e), retryable=True)
                continue
            except (EVisitorUnknownError, EVisitorError) as e:
                reg._handle_failure(log, str(e), retryable=False)
                continue

            log.write({
                'state': 'sent',
                'http_status': 200,
                'response_payload': json.dumps(response, default=str) if response else '',
            })
            reg.write({
                'evisitor_status': 'deregistered',
                'evisitor_deregistered_at': fields.Datetime.now(),
                'last_error': False,
                'next_retry': False,
            })
            reg.message_post(body=_(
                'Gost odjavljen u eVisitor (checkInId: %s).',
                reg.evisitor_submission_id))

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------

    def _prepare_log_vals(self, request_type, payload):
        self.ensure_one()
        return {
            'registration_id': self.id,
            'accommodation_id': self.accommodation_id.id,
            'company_id': (self.company_id or self.env.company).id,
            'request_type': request_type,
            'submitted_at': fields.Datetime.now(),
            'request_payload': json.dumps(payload, default=str) if payload else '',
            'state': 'pending',
        }

    def _log_failure(self, request_type, error_message, retryable,
                     request_payload=None, response_payload=None):
        """Stvori dnevnički zapis o neuspjehu bez pisanja na samu prijavu."""
        self.ensure_one()
        self.env['l10n_hr.evisitor.log'].create({
            'registration_id': self.id,
            'accommodation_id': self.accommodation_id.id,
            'company_id': (self.company_id or self.env.company).id,
            'request_type': request_type,
            'submitted_at': fields.Datetime.now(),
            'request_payload': json.dumps(request_payload, default=str)
                if request_payload else '',
            'response_payload': response_payload or '',
            'state': 'error',
            'error_message': error_message,
            'next_retry': fields.Datetime.now() + timedelta(
                minutes=RETRY_INTERVAL_MINUTES) if retryable else False,
        })

    def _handle_failure(self, log, error_message, retryable,
                        response_payload=None):
        """Ažuriraj dnevnik i prijavu nakon neuspjeha API poziva."""
        self.ensure_one()
        vals = {
            'state': 'error',
            'error_message': error_message,
            'retry_count': self.retry_count + 1,
            'last_error': error_message,
        }
        if response_payload:
            vals_for_log = {'response_payload': response_payload}
        else:
            vals_for_log = {}
        if retryable and self.retry_count + 1 < MAX_RETRIES:
            vals['evisitor_status'] = 'pending'
            vals['next_retry'] = fields.Datetime.now() + timedelta(
                minutes=RETRY_INTERVAL_MINUTES)
        else:
            vals['evisitor_status'] = 'error'
            vals['next_retry'] = False
        self.write(vals)
        log.write({
            'state': 'error',
            'error_message': error_message,
            'next_retry': vals.get('next_retry'),
            **vals_for_log,
        })
        self.message_post(body=_(
            'eViewer greška (%s): %s%s',
            'ponovni pokušaj' if retryable else 'bez ponovnog pokušaja',
            error_message,
            '' if not retryable or self.retry_count + 1 < MAX_RETRIES
            else _(' (dosegnut maksimalan broj pokušaja)')))

    # ---------------------------------------------------------------------
    # Cron jobs
    # ---------------------------------------------------------------------

    @api.model
    def _cron_process_pending(self):
        """Obradi sve prijave sa statusom „Na čekanju”.

        Poziva se svakih 15 minuta (vidi ``data/ir_cron_data.xml``).
        """
        pending = self.search([
            ('evisitor_status', '=', 'pending'),
        ])
        _logger.info('eVisitor cron: processing %d pending registrations', len(pending))
        for reg in pending:
            try:
                reg._evisitor_register()
            except Exception as e:  # noqa: BLE001 — cron must not crash
                _logger.exception(
                    'eVisitor cron: unexpected error processing %s: %s',
                    reg.name, e)

    @api.model
    def _cron_retry_errors(self):
        """Ponovno pošalji prijave sa statusom „Greška” kod kojih je istekao
        ``next_retry`` i koje su označene kao ponovljive (connection error).

        Poziva se svakih 15 minuta (vidi ``data/ir_cron_data.xml``).
        """
        now = fields.Datetime.now()
        # Errors with a scheduled retry are connection-error retries.
        to_retry = self.search([
            ('evisitor_status', '=', 'error'),
            ('next_retry', '!=', False),
            ('next_retry', '<=', now),
        ])
        # Also re-process anything still pending that for some reason
        # wasn't picked up by ``_cron_process_pending``.
        pending = self.search([
            ('evisitor_status', '=', 'pending'),
        ])
        candidates = to_retry | pending
        _logger.info(
            'eVisitor cron: retrying %d registrations (%d errors, %d pending)',
            len(candidates), len(to_retry), len(pending))
        for reg in candidates:
            try:
                # Determine which operation to retry based on prior state.
                if reg.evisitor_submission_id and reg.evisitor_status == 'error':
                    # The error happened on deregistration.
                    reg._evisitor_deregister()
                else:
                    reg._evisitor_register()
            except Exception as e:  # noqa: BLE001 — cron must not crash
                _logger.exception(
                    'eVisitor cron: unexpected error retrying %s: %s',
                    reg.name, e)
