# -*- coding: utf-8 -*-
"""Group booking - ena skupinska rezervacija z N sobami."""
from odoo import _, api, fields, models


class L10nSiGroupBooking(models.Model):
    _name = 'l10n_si.group.booking'
    _description = 'Slovenian Group Booking'
    _inherit = ['mail.thread']
    _order = 'date_from DESC'

    name = fields.Char(required=True, tracking=True)
    number = fields.Char(copy=False, readonly=True, default='/')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # Stranka (agency)
    partner_id = fields.Many2one('res.partner', string='Agencija/Stranka', required=True, tracking=True)
    is_travel_agency = fields.Boolean(string='Travel Agency', default=False)

    # Skupina
    group_name = fields.Char(string='Ime skupine', help='npr. "Izlet srednje šole XY"')
    group_type = fields.Selection(
        selection=[('travel_agency', 'Potovalna agencija'),
                   ('school', 'Šola'),
                   ('corporate', 'Podjetje'),
                   ('sports_team', 'Športna ekipa'),
                   ('family', 'Družina'),
                   ('other', 'Drugo')],
        default='travel_agency',
        required=True,
    )

    # Čas
    date_from = fields.Datetime(required=True, default=fields.Datetime.now, string='Od')
    date_to = fields.Datetime(required=True, string='Do')
    nights = fields.Integer(compute='_compute_nights', store=True)

    # Sobe
    room_count_booked = fields.Integer(required=True, default=10, string='Rezervirano sob')
    room_count_confirmed = fields.Integer(default=0, string='Potrjenih sob',
                                            compute='_compute_room_stats', store=True)
    room_count_available = fields.Integer(default=10, string='Še prostih za rezervacijo',
                                            compute='_compute_room_stats', store=True)
    room_type_id = fields.Many2one('l10n_si.hotel.room.type', required=True, ondelete='restrict')

    # Cena
    group_rate_per_night = fields.Float(required=True, default=60.0, string='Skupinska cena/noč')
    commission_percent = fields.Float(default=10.0, string='Provizija agencije (%)')
    free_leader_every_n = fields.Integer(default=20, string='Brezplačna soba vsakih N gostov',
                                           help='npr. 20 = vsakih 20 gostov 1 brezplačna soba.')

    # Paket
    meal_plan = fields.Selection(
        selection=[('bb', 'B&B (zajtrk)'),
                   ('hb', 'Polpenzion'),
                   ('fb', 'Polni penzion'),
                   ('ai', 'All-inclusive'),
                   ('ro', 'Samo nočitev')],
        default='bb',
        required=True,
    )
    meal_plan_price_per_person = fields.Float(default=15.0)

    # Cut-off
    cutoff_date = fields.Date(required=True, string='Cut-off datum',
                                help='Do tega datuma lahko agencija še spreminja število sob.')
    allocation_release_date = fields.Date(string='Sprostitev neporabljenih sob')

    # Status
    state = fields.Selection(
        selection=[('inquiry', 'Povpraševanje'),
                   ('quoted', 'Ponudba'),
                   ('confirmed', 'Potrjeno'),
                   ('deposit_paid', 'Avans plačan'),
                   ('in_house', 'V hotelu'),
                   ('completed', 'Zaključeno'),
                   ('cancelled', 'Preklicano')],
        default='inquiry',
        tracking=True,
    )

    # Opis
    special_requirements = fields.Text(string='Posebne zahteve (prevoz, diete)')
    internal_notes = fields.Text()

    # Povezave
    rooming_list_ids = fields.One2many('l10n_si.rooming.list', 'group_booking_id', string='Rooming list')
    folio_ids = fields.Many2many('l10n_si.hotel.folio', string='Foliji')

    # Skupni znesek
    total_amount = fields.Monetary(compute='_compute_total', store=True, currency_field='currency_id',
                                     string='Ocenjeni skupni znesek')
    commission_amount = fields.Monetary(compute='_compute_total', store=True, currency_field='currency_id',
                                          string='Provizija')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', '/') == '/':
                vals['number'] = self.env['ir.sequence'].next_by_code('l10n_si.group.booking') or '/'
        return super().create(vals_list)

    @api.depends('date_from', 'date_to')
    def _compute_nights(self):
        for gb in self:
            if gb.date_from and gb.date_to:
                gb.nights = max((gb.date_to - gb.date_from).days, 0)
            else:
                gb.nights = 0

    def _compute_room_stats(self):
        for gb in self:
            gb.room_count_confirmed = len(gb.rooming_list_ids)
            gb.room_count_available = gb.room_count_booked - gb.room_count_confirmed

    @api.depends('nights', 'room_count_booked', 'group_rate_per_night', 'commission_percent', 'free_leader_every_n')
    def _compute_total(self):
        for gb in self:
            total = gb.nights * gb.room_count_booked * gb.group_rate_per_night
            # Free leader rooms
            if gb.free_leader_every_n > 0:
                free_rooms = gb.room_count_booked // gb.free_leader_every_n
                total -= free_rooms * gb.nights * gb.group_rate_per_night
            gb.total_amount = total
            gb.commission_amount = total * (gb.commission_percent / 100)

    def action_send_quote(self):
        self.write({'state': 'quoted'})

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_register_deposit(self):
        self.write({'state': 'deposit_paid'})

    def action_set_in_house(self):
        self.write({'state': 'in_house'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})
