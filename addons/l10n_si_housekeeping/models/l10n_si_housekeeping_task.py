# -*- coding: utf-8 -*-
"""Housekeeping task - ena naloga čiščenja ene sobe."""
from odoo import api, fields, models


class L10nSiHousekeepingTask(models.Model):
    _name = 'l10n_si.housekeeping.task'
    _description = 'Slovenian Housekeeping Task'
    _inherit = ['mail.thread']
    _order = 'scheduled_date, priority DESC, room_id'

    name = fields.Char(compute='_compute_name', store=True)
    number = fields.Char(copy=False, readonly=True, default='/')
    room_id = fields.Many2one('l10n_si.hotel.room', required=True, ondelete='restrict')
    housekeeper_id = fields.Many2one('hr.employee', string='Hišnik',
                                      domain="[('si_is_housekeeper', '=', True)]")
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # Tip naloge
    task_type = fields.Selection(
        selection=[('daily', 'Dnevno čiščenje'),
                   ('checkout', 'Po odjavi gosta'),
                   ('deep', 'Globoko čiščenje'),
                   ('vip', 'VIP priprava'),
                   ('maintenance', 'Pred vzdrževanjem')],
        default='daily',
        required=True,
    )

    # Čas
    scheduled_date = fields.Datetime(required=True, default=fields.Datetime.now)
    started_on = fields.Datetime(readonly=True, copy=False)
    completed_on = fields.Datetime(readonly=True, copy=False)
    duration_minutes = fields.Integer(readonly=True, copy=False,
                                       help='Dejanski čas od začetka do konca.')

    # Priority
    priority = fields.Selection(
        selection=[('0', 'Normalna'),
                   ('1', 'Visoka'),
                   ('2', 'Nujna (check-in čaka)')],
        default='0',
        tracking=True,
    )

    # Status
    state = fields.Selection(
        selection=[('pending', 'V čakalni vrsti'),
                   ('assigned', 'Dodeljeno'),
                   ('in_progress', 'V izvedbi'),
                   ('done', 'Opravljeno'),
                   ('inspected', 'Pregledano'),
                   ('skipped', 'Preskočeno')],
        default='pending',
        tracking=True,
    )

    # Beležke
    notes = fields.Text(string='Opombe hišnika')
    inspection_notes = fields.Text(string='Opombe inšpektorja')
    inspected_by = fields.Many2one('res.users', readonly=True, copy=False)

    # Najdene težave
    found_damages = fields.Boolean(string='Najdene poškodbe', default=False)
    found_lost_items = fields.Boolean(string='Najdeni izgubljeni predmeti', default=False)
    needs_maintenance = fields.Boolean(string='Potrebuje vzdrževanje', default=False)

    # Poraba materiala
    towels_used = fields.Integer(default=0)
    sheets_used = fields.Integer(default=0)
    amenity_kits_used = fields.Integer(default=0)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', '/') == '/':
                vals['number'] = self.env['ir.sequence'].next_by_code('l10n_si.housekeeping.task') or '/'
        return super().create(vals_list)

    @api.depends('number', 'room_id')
    def _compute_name(self):
        for t in self:
            room = t.room_id.number or ''
            t.name = f'{t.number} - soba {room}'

    def action_assign(self):
        self.write({'state': 'assigned'})

    def action_start(self):
        for t in self:
            t.write({
                'state': 'in_progress',
                'started_on': fields.Datetime.now(),
            })

    def action_complete(self):
        from datetime import timedelta
        for t in self:
            duration = 0
            if t.started_on:
                delta = fields.Datetime.now() - t.started_on
                duration = int(delta.total_seconds() / 60)
            t.write({
                'state': 'done',
                'completed_on': fields.Datetime.now(),
                'duration_minutes': duration,
            })
            # Posodobi stanje sobe
            if t.room_id and t.room_id.state == 'cleaning':
                t.room_id.state = 'available'

    def action_inspect(self):
        for t in self:
            t.write({
                'state': 'inspected',
                'inspected_by': self.env.user.id,
            })

    def action_skip(self):
        self.write({'state': 'skipped'})

    @api.model
    def _cron_generate_daily_tasks(self):
        """Dnevni cron ob 6:00 - generira task-e za vse aktivne sobe."""
        rooms = self.env['l10n_si.hotel.room'].search([
            ('active', '=', True),
            ('state', 'in', ['cleaning', 'available']),
        ])
        for room in rooms:
            self.create({
                'room_id': room.id,
                'task_type': 'daily',
                'priority': '1' if room.state == 'cleaning' else '0',
            })
