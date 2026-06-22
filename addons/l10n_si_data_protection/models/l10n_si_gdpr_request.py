# -*- coding: utf-8 -*-
from odoo import api, fields, models


class L10nSiGdprRequest(models.Model):
    _name = 'l10n_si.gdpr.request'
    _description = 'Slovenian GDPR Data Subject Request'
    _inherit = ['mail.thread']
    _order = 'create_date DESC'

    name = fields.Char(compute='_compute_name', store=True)
    number = fields.Char(copy=False, readonly=True, default='/')
    company_id = fields.Many2one('res.company', string='Company',
        default=lambda self: self.env.company, required=True)

    partner_id = fields.Many2one('res.partner', string='Stranka', required=True)
    request_type = fields.Selection(
        selection=[('access', 'Dostop do podatkov (člen 15)'),
                   ('rectification', 'Popravek podatkov (člen 16)'),
                   ('erasure', 'Brisanje podatkov (člen 17)'),
                   ('restriction', 'Omejitev obdelave (člen 18)'),
                   ('portability', 'Prenosljivost podatkov (člen 20)'),
                   ('objection', 'Prigovor (člen 21)'),
                   ('complaint', 'Pritožba (IPP)')],
        required=True, default='access')

    description = fields.Text(required=True)
    received_on = fields.Datetime(default=fields.Datetime.now, readonly=True)
    deadline = fields.Datetime(compute='_compute_deadline', store=True,
        help='GDPR zahteva odgovor v 30 dneh.')

    state = fields.Selection(
        selection=[('new', 'Novo'), ('in_progress', 'V obravnavi'),
                   ('completed', 'Opravljeno'), ('rejected', 'Zavrnjeno')],
        default='new', tracking=True)

    completed_on = fields.Datetime(readonly=True, copy=False)
    handled_by = fields.Many2one('res.users', default=lambda self: self.env.user)
    resolution_notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', '/') == '/':
                vals['number'] = self.env['ir.sequence'].next_by_code('l10n_si.gdpr.request') or '/'
        return super().create(vals_list)

    @api.depends('partner_id', 'received_on', 'request_type')
    def _compute_name(self):
        from datetime import timedelta
        for r in self:
            r.name = f'{r.number} - {r.partner_id.name or ""}'
            if r.received_on:
                r.deadline = r.received_on + timedelta(days=30)

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_complete(self):
        for r in self:
            r.write({'state': 'completed', 'completed_on': fields.Datetime.now()})
            if r.request_type == 'erasure':
                r._execute_erasure()

    def action_reject(self):
        self.write({'state': 'rejected'})

    def _execute_erasure(self):
        """Pravica do brisanja (člen 17 GDPR).
        Anonimizira partnerja (ne briše zaradi knjigovodskih sledi)."""
        for r in self:
            partner = r.partner_id
            # Anonimiziraj osebne podatke, obdrži poslovne
            partner.sudo().write({
                'name': f'[IZBRISANO] - {partner.name[:3]}***',
                'email': False,
                'phone': False,
                'mobile': False,
                'website': False,
                'comment': f'Podatki izbrisani na zahtevo gosta ({r.number}) dne {fields.Datetime.now()}',
            })
            # Umakni vsa soglasja
            self.env['l10n_si.gdpr.consent'].search([
                ('partner_id', '=', partner.id),
                ('state', '=', 'granted'),
            ]).action_withdraw()
