# -*- coding: utf-8 -*-
"""Ticket model — the main helpdesk ticket."""
from datetime import datetime, timedelta

from odoo import _, api, fields, models


class L10nSiHelpdeskTicket(models.Model):
    _name = 'l10n_si.helpdesk.ticket'
    _description = 'Slovenian Helpdesk Ticket'
    _inherit = ['mail.thread']
    _order = 'priority DESC, create_date DESC'

    name = fields.Char(string='Subject', required=True, tracking=True)
    number = fields.Char(string='Number', copy=False, readonly=True, default='/')
    description = fields.Html(required=True)
    team_id = fields.Many2one('l10n_si.helpdesk.team', required=True, tracking=True)
    user_id = fields.Many2one('res.users', string='Assigned to', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True)
    partner_email = fields.Char(related='partner_id.email', store=True)
    partner_phone = fields.Char(related='partner_id.phone', store=True)

    stage_id = fields.Many2one(
        'l10n_si.helpdesk.stage', required=True, tracking=True,
        default=lambda self: self.env['l10n_si.helpdesk.stage'].search(
            [('is_default', '=', True)], limit=1,
        ) or self.env['l10n_si.helpdesk.stage'].search([], limit=1),
    )
    kanban_state = fields.Selection(
        selection=[('normal', 'Normalno'),
                   ('done', 'Pripravljeno'),
                   ('blocked', 'Blokirano')],
        default='normal',
    )

    priority = fields.Selection(
        selection=[('0', 'Nizka'),
                   ('1', 'Srednja'),
                   ('2', 'Visoka'),
                   ('3', 'Nujno')],
        default='1',
        tracking=True,
    )
    tag_ids = fields.Many2many('l10n_si.helpdesk.tag', string='Tags')
    category = fields.Selection(
        selection=[('question', 'Vprašanje'),
                   ('reclamation', 'Reklamacija'),
                   ('technical', 'Tehnična težava'),
                   ('billing', 'Obračun / plačilo'),
                   ('other', 'Drugo')],
        default='question',
    )

    # SLA tracking
    create_date = fields.Datetime(readonly=True)
    first_response_date = fields.Datetime(readonly=True, copy=False)
    closed_date = fields.Datetime(readonly=True, copy=False)
    sla_response_deadline = fields.Datetime(compute='_compute_sla_deadlines', store=True)
    sla_resolution_deadline = fields.Datetime(compute='_compute_sla_deadlines', store=True)
    sla_response_ok = fields.Boolean(compute='_compute_sla_status', store=True)
    sla_resolution_ok = fields.Boolean(compute='_compute_sla_status', store=True)

    # Time tracking
    timesheet_ids = fields.One2many('account.analytic.line', 'l10n_si_helpdesk_ticket_id')
    total_time = fields.Float(compute='_compute_total_time', store=True)

    company_id = fields.Many2one(
        'res.company', related='team_id.company_id', store=True,
    )
    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals_list):
        # Generate ticket number
        for vals in vals_list:
            if vals.get('number', '/') == '/':
                vals['number'] = self.env['ir.sequence'].next_by_code('l10n_si.helpdesk.ticket') or '/'
        tickets = super().create(vals_list)
        # Auto-assign if configured
        for ticket in tickets:
            if ticket.team_id.use_automatic_assignment and not ticket.user_id:
                ticket._auto_assign()
        return tickets

    @api.depends('team_id.sla_response_hours', 'create_date')
    def _compute_sla_deadlines(self):
        for ticket in self:
            if not ticket.create_date or not ticket.team_id:
                continue
            ticket.sla_response_deadline = ticket.create_date + timedelta(
                hours=ticket.team_id.sla_response_hours,
            )
            ticket.sla_resolution_deadline = ticket.create_date + timedelta(
                hours=ticket.team_id.sla_resolution_hours,
            )

    @api.depends('first_response_date', 'sla_response_deadline',
                 'closed_date', 'sla_resolution_deadline')
    def _compute_sla_status(self):
        for ticket in self:
            ticket.sla_response_ok = bool(
                ticket.first_response_date and
                ticket.first_response_date <= ticket.sla_response_deadline
            ) if ticket.first_response_date else False
            ticket.sla_resolution_ok = bool(
                ticket.closed_date and
                ticket.closed_date <= ticket.sla_resolution_deadline
            ) if ticket.closed_date else False

    @api.depends('timesheet_ids.unit_amount')
    def _compute_total_time(self):
        for ticket in self:
            ticket.total_time = sum(ticket.timesheet_ids.mapped('unit_amount'))

    def write(self, vals):
        res = super().write(vals)
        # Track first response: any message_post or stage change to non-default
        if vals.get('stage_id') and not self.first_response_date:
            new_stage = self.env['l10n_si.helpdesk.stage'].browse(vals['stage_id'])
            if new_stage and not new_stage.is_default:
                self.first_response_date = fields.Datetime.now()
        # Track closure
        if vals.get('stage_id'):
            new_stage = self.env['l10n_si.helpdesk.stage'].browse(vals['stage_id'])
            if new_stage and new_stage.is_close:
                self.closed_date = fields.Datetime.now()
        return res

    def _auto_assign(self):
        """Round-robin: assign to the team member with fewest open tickets."""
        self.ensure_one()
        members = self.team_id.member_ids
        if not members:
            return
        # Find member with fewest open tickets
        ticket_counts = {}
        for member in members:
            ticket_counts[member.id] = self.env['l10n_si.helpdesk.ticket'].search_count([
                ('user_id', '=', member.id),
                ('stage_id.is_close', '=', False),
            ])
        assigned = min(members, key=lambda m: ticket_counts[m.id])
        self.user_id = assigned.id


class L10nSiHelpdeskTag(models.Model):
    _name = 'l10n_si.helpdesk.tag'
    _description = 'Slovenian Helpdesk Tag'

    name = fields.Char(required=True, translate=True)
    color = fields.Integer()
    team_ids = fields.Many2many('l10n_si.helpdesk.team', string='Teams')


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    l10n_si_helpdesk_ticket_id = fields.Many2one(
        'l10n_si.helpdesk.ticket', string='Helpdesk Ticket', ondelete='set null',
    )
