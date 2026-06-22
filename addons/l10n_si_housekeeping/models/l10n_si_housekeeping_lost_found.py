# -*- coding: utf-8 -*-
"""Lost & Found - izgubljeni predmeti gostov."""
from odoo import api, fields, models


class L10nSiHousekeepingLostFound(models.Model):
    _name = 'l10n_si.housekeeping.lost.found'
    _description = 'Slovenian Hotel Lost & Found'
    _inherit = ['mail.thread']
    _order = 'found_date DESC'

    name = fields.Char(required=True, translate=True)
    number = fields.Char(copy=False, readonly=True, default='/')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # Kje in kdaj najdeno
    found_date = fields.Datetime(required=True, default=fields.Datetime.now)
    found_by_id = fields.Many2one('hr.employee', string='Najšel', required=True)
    room_id = fields.Many2one('l10n_si.hotel.room', string='Soba')
    location = fields.Char(string='Druga lokacija', help='npr. recepcija, restavracija')

    # Kaj
    description = fields.Text(required=True)
    item_category = fields.Selection(
        selection=[('clothing', 'Obleka/obutev'),
                   ('electronics', 'Elektronika'),
                   ('jewelry', 'Nakit'),
                   ('documents', 'Dokumenti'),
                   ('keys', 'Ključi'),
                   ('medication', 'Zdravila'),
                   ('money', 'Denar'),
                   ('other', 'Drugo')],
        default='other',
        required=True,
    )

    # Lastnik
    partner_id = fields.Many2one('res.partner', string='Gost (če znan)')
    hotel_folio_id = fields.Many2one('l10n_si.hotel.folio', string='Folio gosta')

    # Status
    state = fields.Selection(
        selection=[('found', 'Najdeno'),
                   ('claimed', 'Prevzeto'),
                   ('returned', 'Vrnjeno gostu'),
                   ('disposed', 'Odstavljeno'),
                   ('donated', 'Donirano')],
        default='found',
        tracking=True,
    )

    # Hramba
    storage_location = fields.Char(string='Lokacija hrambe',
                                     help='npr. sef recepcija, omara A3')
    disposal_date = fields.Date(readonly=True, copy=False)
    returned_on = fields.Datetime(readonly=True, copy=False)
    returned_to = fields.Char(string='Prevzel', readonly=True, copy=False)
    return_method = fields.Selection(
        selection=[('pickup', 'Osebni prevzem'),
                   ('mail', 'Pošta'),
                   ('courier', 'Kurir'),
                   ('other', 'Drugo')],
        readonly=True, copy=False,
    )
    notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', '/') == '/':
                vals['name'] = vals.get('name', '/')  # ensure name set
                vals['number'] = self.env['ir.sequence'].next_by_code('l10n_si.housekeeping.lost.found') or '/'
        return super().create(vals_list)

    def action_return_to_guest(self):
        for item in self:
            item.write({
                'state': 'returned',
                'returned_on': fields.Datetime.now(),
            })

    def action_dispose(self):
        for item in self:
            item.write({
                'state': 'disposed',
                'disposal_date': fields.Date.today(),
            })

    def action_donate(self):
        for item in self:
            item.write({
                'state': 'donated',
                'disposal_date': fields.Date.today(),
            })
