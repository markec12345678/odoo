# -*- coding: utf-8 -*-
"""Monthly payslip run wizard — generate payslips for all employees in one batch."""
import calendar
from datetime import date

from odoo import fields, models


class L10nSiPayslipRunWizard(models.TransientModel):
    _name = 'l10n_si.payslip.run.wizard'
    _description = 'Monthly Payslip Run'

    year = fields.Integer(required=True, default=lambda self: fields.Date.today().year)
    month = fields.Integer(required=True, default=lambda self: fields.Date.today().month)
    structure_id = fields.Many2one('l10n_si.payroll.structure', required=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )
    employee_ids = fields.Many2many('hr.employee', string='Employees')

    def action_generate(self):
        """Generate one payslip per selected employee for the given month."""
        self.ensure_one()
        Payslip = self.env['l10n_si.payslip']

        # Compute month range
        date_from = date(self.year, self.month, 1)
        last_day = calendar.monthrange(self.year, self.month)[1]
        date_to = date(self.year, self.month, last_day)

        employees = self.employee_ids or self.env['hr.employee'].search([
            ('company_id', '=', self.company_id.id),
            ('active', '=', True),
        ])

        # Batch-search all contracts for all employees at once (avoids N+1)
        all_contracts = self.env['l10n_si.hr.contract'].search([
            ('employee_id', 'in', employees.ids),
            ('state', '=', 'open'),
            ('date_start', '<=', date_to),
            '|', ('date_end', '=', False), ('date_end', '>=', date_from),
        ])
        # Build a dict: employee_id -> contract (take first if multiple)
        contracts_by_emp = {}
        for contract in all_contracts:
            if contract.employee_id.id not in contracts_by_emp:
                contracts_by_emp[contract.employee_id.id] = contract

        for emp in employees:
            contract = contracts_by_emp.get(emp.id)
            if not contract:
                continue
            # Default bruto from contract wage
            bruto = contract.wage or self.company_id.si_payroll_minimum_bruto

            Payslip.create({
                'employee_id': emp.id,
                'contract_id': contract.id,
                'structure_id': self.structure_id.id,
                'company_id': self.company_id.id,
                'date_from': date_from,
                'date_to': date_to,
                'bruto_amount': bruto,
                'work_days': 22,  # average working days in a month
                'work_hours': 176,  # 22 * 8
            })
        return {'type': 'ir.actions.act_window_close'}
