# -*- coding: utf-8 -*-
from odoo import api, fields, models


class L10nSiConciergeRequest(models.Model):
    _name = 'l10n_si.concierge.request'
    _description = 'Slovenian Concierge Request'
    _inherit = ['mail.thread']
    _order = 'create_date DESC'

    name = fields.Char(required=True, string='Naslov')
    number = fields.Char(copy=False, readonly=True, default='/')
    company_id = fields.Many2one('res.company', string='Company',
        default=lambda self: self.env.company, required=True)

    partner_id = fields.Many2one('res.partner', string='Gost', required=True)
    hotel_folio_id = fields.Many2one('l10n_si.hotel.folio', string='Folio')

    request_type = fields.Selection(
        selection=[('excursion', 'Izlet/vodenje'),
                   ('tickets', 'Vstopnice (gledališče, koncert)'),
                   ('restaurant', 'Rezervacija restavracije'),
                   ('transport', 'Prevoz/taxi'),
                   ('spa', 'Wellness/masaža'),
                   ('shopping', 'Nakupovanje'),
                   ('medical', 'Medicinska pomoč'),
                   ('business', 'Poslovne storitve'),
                   ('other', 'Drugo')],
        required=True, default='other')

    description = fields.Text(required=True)
    priority = fields.Selection([('0','Normalna'),('1','Visoka'),('2','Nujna')], default='0')

    state = fields.Selection(
        selection=[('new', 'Novo'), ('in_progress', 'V obravnavi'),
                   ('completed', 'Opravljeno'), ('cancelled', 'Preklicano')],
        default='new', tracking=True)

    cost = fields.Float(default=0.0, string='Strošek (EUR)')
    charge_to_folio = fields.Boolean(default=True, string='Zaračunaj na folio')
    completed_on = fields.Datetime(readonly=True, copy=False)
    handled_by = fields.Many2one('res.users', default=lambda self: self.env.user)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', '/') == '/':
                vals['number'] = self.env['ir.sequence'].next_by_code('l10n_si.concierge.request') or '/'
        return super().create(vals_list)

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_complete(self):
        for r in self:
            r.write({'state': 'completed', 'completed_on': fields.Datetime.now()})
            if r.charge_to_folio and r.hotel_folio_id and r.cost > 0:
                self.env['l10n_si.hotel.folio.line'].create({
                    'folio_id': r.hotel_folio_id.id,
                    'description': f'Concierge: {r.name}',
                    'quantity': 1,
                    'unit_price': r.cost,
                })

    def action_cancel(self):
        self.write({'state': 'cancelled'})
