# -*- coding: utf-8 -*-
"""Maintenance request - prijava napake."""
from datetime import timedelta

from odoo import api, fields, models


class L10nSiMaintenanceRequest(models.Model):
    _name = 'l10n_si.maintenance.request'
    _description = 'Slovenian Maintenance Request'
    _inherit = ['mail.thread']
    _order = 'create_date DESC'

    name = fields.Char(required=True, string='Naslov')
    number = fields.Char(copy=False, readonly=True, default='/')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # Kdo je prijavil
    partner_id = fields.Many2one('res.partner', string='Gost (če gost prijavil)')
    reported_by_user_id = fields.Many2one('res.users', string='Prijavil (zaposleni)',
                                            default=lambda self: self.env.user)
    reported_by_employee_id = fields.Many2one('hr.employee', string='Prijavil (zaposleni - povezava)')
    source = fields.Selection(
        selection=[('guest_portal', 'Gost preko portala'),
                   ('housekeeping', 'Hišnik'),
                   ('reception', 'Recepcija'),
                   ('technician', 'Tehnik'),
                   ('inspection', 'Inšpekcija')],
        default='reception',
        required=True,
    )

    # Lokacija
    room_id = fields.Many2one('l10n_si.hotel.room', string='Soba')
    venue_id = fields.Many2one('l10n_si.event.venue', string='Venue')
    location_other = fields.Char(string='Druga lokacija')

    # Kaj
    category = fields.Selection(
        selection=[('electrical', 'Elektrika'),
                   ('plumbing', 'Vodovod'),
                   ('hvac', 'Klima/ogrevanje'),
                   ('furniture', 'Pohištvo'),
                   ('appliance', 'Belotehnika'),
                   ('structural', 'Stavba'),
                   ('cleanliness', 'Čistoča'),
                   ('other', 'Drugo')],
        default='other',
        required=True,
    )
    description = fields.Html(required=True)
    photos_ids = fields.One2many('l10n_si.maintenance.request.photo', 'request_id', string='Fotografije')

    # Priority + SLA
    priority = fields.Selection(
        selection=[('0', 'Nizka (7 dni)'),
                   ('1', 'Normalna (24h)'),
                   ('2', 'Visoka (4h)'),
                   ('3', 'Kritična (1h)')],
        default='1',
        required=True,
        tracking=True,
    )
    sla_deadline = fields.Datetime(compute='_compute_sla', store=True)

    # Tehnik
    assigned_technician_id = fields.Many2one('hr.employee', string='Tehnik',
                                                domain="[('si_is_technician', '=', True)]")

    # Status
    state = fields.Selection(
        selection=[('reported', 'Prijavljeno'),
                   ('assigned', 'Dodeljeno'),
                   ('in_progress', 'V obravnavi'),
                   ('waiting_parts', 'Čaka rezervne dele'),
                   ('resolved', 'Opravljeno'),
                   ('verified', 'Preverjeno'),
                   ('closed', 'Zaprto'),
                   ('cancelled', 'Preklicano')],
        default='reported',
        tracking=True,
    )

    # Čas
    reported_on = fields.Datetime(default=fields.Datetime.now, readonly=True)
    started_on = fields.Datetime(readonly=True, copy=False)
    resolved_on = fields.Datetime(readonly=True, copy=False)
    verified_on = fields.Datetime(readonly=True, copy=False)
    resolution_time_hours = fields.Float(compute='_compute_resolution_time', store=True)

    # Rešitev
    resolution_description = fields.Text(string='Opis rešitve')
    parts_used = fields.Text(string='Porabljeni deli')
    cost = fields.Float(default=0.0)
    verified_by = fields.Many2one('res.users', readonly=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', '/') == '/':
                vals['number'] = self.env['ir.sequence'].next_by_code('l10n_si.maintenance.request') or '/'
        return super().create(vals_list)

    @api.depends('reported_on', 'priority')
    def _compute_sla(self):
        sla_hours = {'0': 168, '1': 24, '2': 4, '3': 1}  # hours per priority
        for r in self:
            hours = sla_hours.get(r.priority, 24)
            if r.reported_on:
                r.sla_deadline = r.reported_on + timedelta(hours=hours)
            else:
                r.sla_deadline = False

    @api.depends('reported_on', 'resolved_on')
    def _compute_resolution_time(self):
        for r in self:
            if r.reported_on and r.resolved_on:
                delta = r.resolved_on - r.reported_on
                r.resolution_time_hours = delta.total_seconds() / 3600.0
            else:
                r.resolution_time_hours = 0.0

    def action_assign(self):
        self.write({'state': 'assigned'})

    def action_start(self):
        for r in self:
            r.write({
                'state': 'in_progress',
                'started_on': fields.Datetime.now(),
            })

    def action_waiting_parts(self):
        self.write({'state': 'waiting_parts'})

    def action_resolve(self):
        for r in self:
            r.write({
                'state': 'resolved',
                'resolved_on': fields.Datetime.now(),
            })

    def action_verify(self):
        for r in self:
            r.write({
                'state': 'verified',
                'verified_by': self.env.user.id,
                'verified_on': fields.Datetime.now(),
            })

    def action_close(self):
        self.write({'state': 'closed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})


class L10nSiMaintenanceRequestPhoto(models.Model):
    _name = 'l10n_si.maintenance.request.photo'
    _description = 'Slovenian Maintenance Request Photo'

    request_id = fields.Many2one('l10n_si.maintenance.request', required=True, ondelete='cascade')
    image = fields.Binary(required=True)
    caption = fields.Char()
    taken_on = fields.Datetime(default=fields.Datetime.now)
