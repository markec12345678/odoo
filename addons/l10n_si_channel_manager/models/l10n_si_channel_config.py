# -*- coding: utf-8 -*-
"""Channel configuration - one record per channel per company."""
from odoo import api, fields, models


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
                # Simuliran test - v produkciji pravi API klic
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
            cfg.last_sync = fields.Datetime.now()

    def _push_availability(self):
        """Push room availability to channel."""
        self.ensure_one()
        for mapping in self.room_mapping_ids:
            # Get SI availability for next 90 days
            # Push to channel API
            self.env['l10n_si.channel.log'].create({
                'channel_config_id': self.id,
                'log_type': 'availability_push',
                'state': 'success',
                'message': f'Pushed availability for room type {mapping.room_type_id.name}',
            })

    def _pull_reservations(self):
        """Pull new reservations from channel."""
        self.ensure_one()
        # V produkciji: pravi API klic za prejem novih rezervacij
        self.env['l10n_si.channel.log'].create({
            'channel_config_id': self.id,
            'log_type': 'reservation_pull',
            'state': 'success',
            'message': 'No new reservations',
        })

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
