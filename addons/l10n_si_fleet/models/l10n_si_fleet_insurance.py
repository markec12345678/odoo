# -*- coding: utf-8 -*-
"""Insurance log — zavarovanja."""
from odoo import fields, models


class L10nSiFleetInsurance(models.Model):
    _name = 'l10n_si.fleet.insurance'
    _description = 'Slovenian Fleet Insurance'
    _order = 'date_from DESC'

    name = fields.Char(required=True)
    vehicle_id = fields.Many2one('fleet.vehicle', required=True, ondelete='restrict')
    insurance_company = fields.Char(string='Zavarovalnica', required=True)
    policy_number = fields.Char(string='Polica št.', required=True)
    insurance_type = fields.Selection(
        selection=[('ao', 'Avtomobilska odgovornost (AO)'),
                   ('kasko', 'Kasko'),
                   ('ao_kasko', 'AO + Kasko'),
                   ('potniki', 'Zavarovanje potnikov'),
                   ('nezgoda', 'Zavarovanje nezgode')],
        default='ao',
        required=True,
    )
    date_from = fields.Date(string='Velja od', required=True)
    date_to = fields.Date(string='Velja do', required=True)
    premium = fields.Float(string='Premija (€)')
    deductible = fields.Float(string='Lastna udeležba (€)')
    vendor_id = fields.Many2one('res.partner', string='Agent')
    notes = fields.Text()
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )
    active = fields.Boolean(default=True)
