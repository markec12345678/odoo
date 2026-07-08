# -*- coding: utf-8 -*-
from odoo import fields, models


class HrContract(models.Model):
    _name = 'l10n_si.hr.contract'
    _description = 'SI HR Contract (standalone)'

    si_work_hours_per_week = fields.Float(
        string='Tedenske ure',
        default=40.0,
        help='Full-time = 40, part-time < 40.',
    )
    si_job_title_code = fields.Char(
        string='Koda poklica (KMCP)',
        help='Klasifikacija poklicev — potrebna za REK-1.',
    )
    si_employment_type = fields.Selection(
        selection=[('permanent_full', 'Trajno polni čas'),
                   ('permanent_part', 'Trajno delni čas'),
                   ('fixed_full', 'Določeni čas polni'),
                   ('fixed_part', 'Določeni čas delni'),
                   ('student', 'Študentsko delo'),
                   ('author', 'Avtorska pogodba')],
        default='permanent_full',
        string='Tip zaposlitve',
    )
    si_probation_until = fields.Date(string='Preizkusna doba do')
