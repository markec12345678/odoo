# -*- coding: utf-8 -*-
from odoo import api, fields, models


class L10nSiTransportBooking(models.Model):
    _name = 'l10n_si.transport.booking'
    _description = 'Slovenian Transport Booking'
    _inherit = ['mail.thread']
    _order = 'pickup_datetime DESC'

    name = fields.Char(compute='_compute_name', store=True)
    number = fields.Char(copy=False, readonly=True, default='/')
    company_id = fields.Many2one('res.company', string='Company',
        default=lambda self: self.env.company, required=True)

    partner_id = fields.Many2one('res.partner', string='Gost', required=True)
    hotel_folio_id = fields.Many2one('l10n_si.hotel.folio', string='Folio')

    transport_type = fields.Selection(
        selection=[('airport_shuttle', 'Letališki shuttle'),
                   ('private_transfer', 'Zasebni transfer'),
                   ('excursion_bus', 'Izlet z avtobusom'),
                   ('taxi', 'Taxi'),
                   ('car_rental', 'Najem avta'),
                   ('limousine', 'Limuzina')],
        required=True, default='airport_shuttle')

    # Pickup
    pickup_datetime = fields.Datetime(required=True, default=fields.Datetime.now)
    pickup_location = fields.Char(required=True, string='Lokacija prevzema')
    dropoff_location = fields.Char(required=True, string='Lokacija odstavitve')

    # Passengers
    passengers = fields.Integer(default=2, required=True)
    luggage_pieces = fields.Integer(default=2)

    # Vehicle
    fleet_vehicle_id = fields.Many2one('fleet.vehicle', string='Vozilo')
    driver_id = fields.Many2one('hr.employee', string='Voznik')

    # Price
    price = fields.Float(required=True, default=30.0)
    charge_to_folio = fields.Boolean(default=True)

    # Status
    state = fields.Selection(
        selection=[('draft', 'Osnutek'), ('confirmed', 'Potrjeno'),
                   ('in_progress', 'V izvedbi'), ('completed', 'Opravljeno'),
                   ('cancelled', 'Preklicano')],
        default='draft', tracking=True)

    flight_number = fields.Char(string='Let (za letališki shuttle)')
    notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', '/') == '/':
                vals['number'] = self.env['ir.sequence'].next_by_code('l10n_si.transport.booking') or '/'
        return super().create(vals_list)

    @api.depends('number', 'partner_id', 'pickup_datetime')
    def _compute_name(self):
        for b in self:
            b.name = f'{b.number} - {b.partner_id.name or ""} - {b.pickup_datetime or ""}'

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_complete(self):
        for b in self:
            b.write({'state': 'completed'})
            if b.charge_to_folio and b.hotel_folio_id:
                self.env['l10n_si.hotel.folio.line'].create({
                    'folio_id': b.hotel_folio_id.id,
                    'description': f'{b.transport_type}: {b.pickup_location} → {b.dropoff_location}',
                    'quantity': 1,
                    'unit_price': b.price,
                })

    def action_cancel(self):
        self.write({'state': 'cancelled'})
