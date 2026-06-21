# -*- coding: utf-8 -*-
"""Maintenance log — servisi."""
from odoo import fields, models


class L10nSiFleetMaintenance(models.Model):
    _name = 'l10n_si.fleet.maintenance'
    _description = 'Slovenian Fleet Maintenance'
    _inherit = ['mail.thread']
    _order = 'date DESC'

    name = fields.Char(required=True, string='Opis servisnega dela')
    vehicle_id = fields.Many2one('fleet.vehicle', required=True, ondelete='restrict')
    date = fields.Datetime(required=True, default=fields.Datetime.now)
    maintenance_type = fields.Selection(
        selection=[('scheduled', 'Načrtovani'),
                   ('corrective', 'Popravilo'),
                   ('inspection', 'Pregled')],
        default='scheduled',
        required=True,
    )
    odometer = fields.Integer(string='Stanje števca (km)')
    vendor_id = fields.Many2one('res.partner', string='Servis')
    cost = fields.Float(string='Strošek (€)', default=0.0)
    description = fields.Text(string='Opis opravljenih del')
    invoice_number = fields.Char(string='Številka računa')
    next_service_odometer = fields.Integer(string='Naslednji servis pri (km)')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )
    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('done', 'Opravljeno'),
                   ('cancelled', 'Preklicano')],
        default='draft',
    )

    def action_done(self):
        for rec in self:
            rec.state = 'done'
