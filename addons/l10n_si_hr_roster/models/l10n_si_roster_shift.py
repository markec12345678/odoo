# -*- coding: utf-8 -*-
"""Shift definition - jutranja, popoldanska, nočna, celodnevna."""
from odoo import api, fields, models


class L10nSiRosterShift(models.Model):
    _name = 'l10n_si.roster.shift'
    _description = 'Slovenian Roster Shift'
    _order = 'start_hour'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, size=8)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # Časovni okvir (znotraj dneva)
    start_hour = fields.Float(required=True, default=6.0,
                                help='6.0 = 06:00. 14.5 = 14:30.')
    end_hour = fields.Float(required=True, default=14.0)
    duration_hours = fields.Float(compute='_compute_duration', store=True)

    # Tip izmene
    shift_type = fields.Selection(
        selection=[('morning', 'Jutranja'),
                   ('afternoon', 'Popoldanska'),
                   ('night', 'Nočna'),
                   ('full_day', 'Celodnevna'),
                   ('split', 'Razdeljena (2 dela)')],
        required=True,
        default='morning',
    )

    # Barva za koledar
    color = fields.Integer(default=0)

    # Zahtevana delovna mesta
    required_job_positions = fields.Char(string='Zahtevana delovna mesta',
                                            help='npr. "recepcija, hišništvo"')

    # Premija
    night_premium_percent = fields.Float(default=0.0, string='Nočna premija (%)')
    weekend_premium_percent = fields.Float(default=0.0, string='Vikend premija (%)')
    holiday_premium_percent = fields.Float(default=50.0, string='Praznična premija (%)')

    @api.depends('start_hour', 'end_hour')
    def _compute_duration(self):
        for s in self:
            if s.end_hour >= s.start_hour:
                s.duration_hours = s.end_hour - s.start_hour
            else:
                # Preko polnoči (nočna)
                s.duration_hours = (24 - s.start_hour) + s.end_hour

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 'Code must be unique per company.'),
    ]
