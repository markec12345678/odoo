# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    si_payroll_minimum_bruto = fields.Float(
        string='Minimalna bruto plača (€)',
        default=1277.00,
        help='Per ZMinP. Update annually by Jan 1st.',
    )
    si_payroll_injury_rate = fields.Float(
        string='Stopnja poškodb (%)',
        default=0.53,
        help='Employer injury insurance rate. Varies by activity (0.10-3.50%).',
    )
    si_payroll_auto_m4 = fields.Boolean(
        string='Auto-generate M4',
        default=True,
        help='Generate M4 report automatically on the 1st of each month for the previous period.',
    )
