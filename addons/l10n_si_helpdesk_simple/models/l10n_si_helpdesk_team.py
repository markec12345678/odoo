# -*- coding: utf-8 -*-
from odoo import fields, models


class L10nSiHelpdeskTeam(models.Model):
    _name = 'l10n_si.helpdesk.team'
    _description = 'Slovenian Helpdesk Team'
    _inherit = ['mail.thread']
    _order = 'sequence, name'

    name = fields.Char(required=True, translate=True, tracking=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )
    description = fields.Html()

    # SLA
    sla_response_hours = fields.Float(
        string='SLA odgovor (ure)', default=4.0,
        help='Time to first response. ZVPot requires 8 days for reclamations.',
    )
    sla_resolution_hours = fields.Float(
        string='SLA rešitev (ure)', default=48.0,
        help='Time to resolve the ticket.',
    )

    # Members
    member_ids = fields.Many2many('res.users', string='Members')
    leader_id = fields.Many2one('res.users', string='Team Leader')

    # Workflow
    stage_ids = fields.Many2many(
        'l10n_si.helpdesk.stage', string='Stages',
        default=lambda self: self.env['l10n_si.helpdesk.stage'].search([]),
    )
    use_automatic_assignment = fields.Boolean(
        string='Samodejna dodelitev',
        help='Round-robin auto-assign new tickets to team members.',
        default=False,
    )

    # Mail alias
    alias_id = fields.Many2one('mail.alias', string='Alias', copy=False)
    use_alias = fields.Boolean(
        string='Incoming email alias',
        help='Tickets created automatically from emails sent to this alias.',
    )

    ticket_count = fields.Integer(compute='_compute_ticket_count')
    open_ticket_count = fields.Integer(compute='_compute_ticket_count')

    def _compute_ticket_count(self):
        Ticket = self.env['l10n_si.helpdesk.ticket']
        for team in self:
            team.ticket_count = Ticket.search_count([('team_id', '=', team.id)])
            team.open_ticket_count = Ticket.search_count([
                ('team_id', '=', team.id),
                ('stage_id.is_close', '=', False),
            ])

    def _compute_alias_model(self):
        return 'l10n_si.helpdesk.ticket'

    def _compute_alias_values(self):
        return {'alias_defaults': "{'team_id': %d}" % self.id}

    def action_view_tickets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tickets',
            'res_model': 'l10n_si.helpdesk.ticket',
            'view_mode': 'list,form',
            'domain': [('team_id', '=', self.id)],
        }
