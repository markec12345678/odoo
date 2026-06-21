# -*- coding: utf-8 -*-
"""Payroll structure: defines what rules apply to a payslip."""
from odoo import fields, models


class L10nSiPayrollStructure(models.Model):
    """A payroll structure is a set of rules applied to a payslip.

    Default structures:
    - MESECNA_PLACA: standard monthly salary
    - STUDENTsko_DEL0: student work (no contributions, 5% withholding)
    - AVTORSKA_POGODBA: author contract (15% expense recognition)
    - BOLNISKA: sick leave compensation
    """
    _name = 'l10n_si.payroll.structure'
    _description = 'Slovenian Payroll Structure'
    _order = 'name'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, size=16)
    description = fields.Text()
    rule_ids = fields.One2many(
        'l10n_si.payroll.rule', 'structure_id', string='Rules',
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company,
    )

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)',
         'Structure code must be unique per company.'),
    ]
