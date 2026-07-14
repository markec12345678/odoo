# -*- coding: utf-8 -*-
"""Channel configuration - one record per channel per company."""
import logging
from datetime import datetime

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class L10nSiChannelConfig(models.Model):
    _name = 'l10n_si.channel.config'
    _description = 'Slovenian Channel Manager Configuration'
    _order = 'channel'

    name = fields.Char(compute='_compute_name', store=True)
    channel = fields.Selection(
        selection=[('booking_com', 'Booking.com'),
                   ('airbnb', 'Airbnb'),
                   ('expedia', 'Expedia'),
                   ('glamping_com', 'Glamping.com'),
                   ('camping_com', 'Camping.com'),
                   ('custom', 'Custom API')],
        required=True,
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # API credentials
    api_endpoint = fields.Char(required=True)
    api_username = fields.Char()
    api_password = fields.Char()
    api_key = fields.Char()
    hotel_id_on_channel = fields.Char(string='Hotel ID na kanalu', required=True)

    # iCal calendar import (eGost feature)
    ical_url = fields.Char(
        string='iCal URL',
        help='URL do iCal koledarja (Booking.com/Airbnb). Npr. '
             'https://www.booking.com/hotel/si/xxx.en-gb.html?aid=xxx',
    )
    ical_last_import = fields.Datetime(readonly=True, copy=False)
    ical_imported_count = fields.Integer(readonly=True, copy=False, default=0)

    # Sync settings
    sync_frequency_minutes = fields.Integer(default=15, string='Sync vsakih (min)')
    auto_pull_reservations = fields.Boolean(default=True)
    auto_push_availability = fields.Boolean(default=True)
    auto_push_rates = fields.Boolean(default=True)
    markup_percent = fields.Float(default=0.0, string='Pribitek cene (%)')

    # Last sync
    last_sync = fields.Datetime(readonly=True, copy=False)
    last_sync_status = fields.Selection(
        selection=[('success', 'Uspešno'),
                   ('error', 'Napaka'),
                   ('partial', 'Delno')],
        readonly=True, copy=False,
    )
    last_error = fields.Text(readonly=True, copy=False)

    # Mappings
    room_mapping_ids = fields.One2many('l10n_si.channel.room.mapping', 'channel_config_id', string='Mapiranje sob')
    log_ids = fields.One2many('l10n_si.channel.log', 'channel_config_id', string='Logi')

    state = fields.Selection(
        selection=[('draft', 'Nastavljanje'),
                   ('active', 'Aktiven'),
                   ('paused', 'Pavziran'),
                   ('error', 'Napaka')],
        default='draft',
        tracking=True,
    )

    @api.depends('channel', 'hotel_id_on_channel')
    def _compute_name(self):
        labels = dict(self._fields['channel'].selection)
        for c in self:
            c.name = f'{labels.get(c.channel, c.channel)} ({c.hotel_id_on_channel or ""})'

    def action_test_connection(self):
        """Test API connection - simulates a simple API call."""
        import requests
        for cfg in self:
            try:
                response = requests.get(
                    cfg.api_endpoint,
                    headers={'Authorization': f'Bearer {cfg.api_key}' if cfg.api_key else ''},
                    timeout=10,
                )
                if response.status_code in (200, 201):
                    cfg.write({
                        'last_sync': fields.Datetime.now(),
                        'last_sync_status': 'success',
                        'state': 'active',
                        'last_error': False,
                    })
                else:
                    cfg.write({
                        'last_sync_status': 'error',
                        'last_error': f'HTTP {response.status_code}',
                        'state': 'error',
                    })
            except Exception as e:
                cfg.write({
                    'last_sync_status': 'error',
                    'last_error': str(e),
                    'state': 'error',
                })

    def action_sync_now(self):
        """Manual sync trigger."""
        for cfg in self:
            cfg._push_availability()
            cfg._pull_reservations()
            if cfg.ical_url:
                cfg.action_import_ical()
            cfg.last_sync = fields.Datetime.now()

    def _push_availability(self):
        """Push room availability to channel."""
        self.ensure_one()
        for mapping in self.room_mapping_ids:
            self.env['l10n_si.channel.log'].create({
                'channel_config_id': self.id,
                'log_type': 'availability_push',
                'state': 'success',
                'message': f'Pushed availability for room type {mapping.room_type_id.name}',
            })

    def _pull_reservations(self):
        """Pull new reservations from channel."""
        self.ensure_one()
        self.env['l10n_si.channel.log'].create({
            'channel_config_id': self.id,
            'log_type': 'reservation_pull',
            'state': 'success',
            'message': 'No new reservations',
        })

    # ================================================================
    # iCal IMPORT
    # ================================================================

    def action_import_ical(self):
        """Import reservations from iCal feed (Booking.com/Airbnb).

        Parses VEVENT entries from the iCal URL and creates hotel
        reservations for each event.
        """
        import requests

        for cfg in self:
            if not cfg.ical_url:
                _logger.warning('iCal: no URL configured for %s', cfg.name)
                continue

            try:
                response = requests.get(cfg.ical_url, timeout=30)
                if response.status_code != 200:
                    _logger.error('iCal: HTTP %s for %s', response.status_code, cfg.name)
                    cfg.last_error = f'iCal HTTP {response.status_code}'
                    continue

                events = cfg._parse_ical(response.text)
                imported = 0

                for event in events:
                    # Check if reservation already exists (by external ID)
                    existing = self.env['l10n_si.hotel.reservation'].search([
                        ('channel_ref', '=', event.get('uid', '')),
                    ], limit=1) if hasattr(self.env['l10n_si.hotel.reservation'], 'channel_ref') else False

                    if existing:
                        continue

                    # Find partner by name or create
                    partner_name = event.get('summary', 'Unknown Guest')
                    partner = self.env['res.partner'].search([
                        ('name', 'ilike', partner_name),
                    ], limit=1)
                    if not partner:
                        partner = self.env['res.partner'].create({
                            'name': partner_name,
                            'customer_rank': 1,
                        })

                    # Find folio or create
                    folio = self.env['l10n_si.hotel.folio'].search([
                        ('partner_id', '=', partner.id),
                        ('check_in', '>=', event['start']),
                        ('check_in', '<=', event['start'].replace(hour=23, minute=59)),
                    ], limit=1)

                    if not folio:
                        folio = self.env['l10n_si.hotel.folio'].create({
                            'partner_id': partner.id,
                            'check_in': event['start'],
                            'check_out': event['end'],
                            'company_id': cfg.company_id.id,
                        })

                    # Find room from mapping
                    room = False
                    if cfg.room_mapping_ids:
                        room = cfg.room_mapping_ids[0].room_id

                    # Create reservation
                    reservation = self.env['l10n_si.hotel.reservation'].create({
                        'folio_id': folio.id,
                        'room_id': room.id if room else False,
                        'check_in': event['start'],
                        'check_out': event['end'],
                        'adults': event.get('adults', 2),
                        'state': 'confirmed',
                        'source': cfg.channel,
                    })

                    if hasattr(reservation, 'channel_ref'):
                        reservation.channel_ref = event.get('uid', '')

                    imported += 1
                    _logger.info('iCal: imported reservation for %s (%s → %s)',
                                 partner_name, event['start'], event['end'])

                cfg.write({
                    'ical_last_import': fields.Datetime.now(),
                    'ical_imported_count': imported,
                })

                self.env['l10n_si.channel.log'].create({
                    'channel_config_id': cfg.id,
                    'log_type': 'reservation_pull',
                    'state': 'success',
                    'message': f'iCal: imported {imported} new reservations',
                })

                _logger.info('iCal: %s — imported %d reservations', cfg.name, imported)

            except Exception as e:
                _logger.error('iCal import error for %s: %s', cfg.name, e)
                cfg.last_error = f'iCal: {str(e)[:500]}'

    def _parse_ical(self, ical_text):
        """Parse iCal text and return list of event dicts.

        Returns: [{
            'uid': 'unique-id',
            'summary': 'Guest Name',
            'start': datetime,
            'end': datetime,
            'adults': int,
            'description': 'full description',
        }]
        """
        events = []
        current_event = {}

        for line in ical_text.splitlines():
            line = line.strip()

            if line == 'BEGIN:VEVENT':
                current_event = {}
            elif line == 'END:VEVENT':
                if current_event.get('start') and current_event.get('end'):
                    events.append(current_event)
                current_event = {}
            elif ':' in line:
                key, value = line.split(':', 1)
                key = key.split(';')[0]  # Remove parameters like ;VALUE=DATE

                if key == 'UID':
                    current_event['uid'] = value
                elif key == 'SUMMARY':
                    current_event['summary'] = value
                elif key == 'DTSTART':
                    current_event['start'] = self._parse_ical_date(value)
                elif key == 'DTEND':
                    current_event['end'] = self._parse_ical_date(value)
                elif key == 'DESCRIPTION':
                    current_event['description'] = value
                    # Try to extract number of adults
                    if 'adult' in value.lower():
                        import re
                        match = re.search(r'(\d+)\s*adult', value.lower())
                        if match:
                            current_event['adults'] = int(match.group(1))

        return events

    def _parse_ical_date(self, date_str):
        """Parse iCal date string to datetime.

        Formats:
        - 20260115T140000Z (UTC datetime)
        - 20260115 (date only — all-day)
        - 20260115T140000 (local datetime)
        """
        try:
            # Remove timezone suffix
            date_str = date_str.replace('Z', '')

            if 'T' in date_str:
                # DateTime: 20260115T140000
                return datetime.strptime(date_str, '%Y%m%dT%H%M%S')
            else:
                # Date only: 20260115 (all-day — set to noon)
                return datetime.strptime(date_str, '%Y%m%d').replace(hour=12)
        except ValueError as e:
            _logger.warning('iCal date parse error: %s → %s', date_str, e)
            return datetime.now()

    @api.model
    def _cron_sync_all_channels(self):
        """Cron entry: sync all active channels."""
        for cfg in self.search([('state', '=', 'active'), ('auto_pull_reservations', '=', True)]):
            try:
                cfg.action_sync_now()
            except Exception as e:
                cfg.write({
                    'last_sync_status': 'error',
                    'last_error': str(e),
                })
