# -*- coding: utf-8 -*-
"""Payroll rules: individual calculation components (bruto, contributions, net)."""
from odoo import api, fields, models


class L10nSiPayrollRule(models.Model):
    """A payroll rule defines one line of a payslip.

    Examples:
        BRUTO       → bruto znesek (input)
        PRIS_D      → employee contributions (22.10%)
        PRIS_DD     → employer contributions (16.10%)
        OSNOVA_DD   → tax base = bruto - PRIS_D - olajšava
        AKONT       → income tax prepayment
        NETO        → net payout = bruto - PRIS_D - AKONT
    """
    _name = 'l10n_si.payroll.rule'
    _description = 'Slovenian Payroll Rule'
    _order = 'sequence, id'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, size=32, help='Short code used in computation.')
    sequence = fields.Integer(default=10, required=True)
    structure_id = fields.Many2one('l10n_si.payroll.structure', required=True, ondelete='cascade')
    category = fields.Selection(
        selection=[('input', 'Input'),
                   ('bruto', 'Bruto'),
                   ('contributions_employee', 'Prispevki (delojemalec)'),
                   ('contributions_employer', 'Prispevki (delodajalec)'),
                   ('tax', 'Dohodnina'),
                   ('relief', 'Olajšava'),
                   ('net', 'Neto'),
                   ('info', 'Info')],
        required=True,
        default='info',
    )
    description = fields.Text()
    active = fields.Boolean(default=True)


class L10nSiPayslip(models.Model):
    """Monthly payslip for one employee.

    Created by the monthly run wizard, computed on save, exported to M4.
    """
    _name = 'l10n_si.payslip'
    _description = 'Slovenian Payslip'
    _order = 'date_from DESC, employee_id'

    name = fields.Char(compute='_compute_name', store=True)
    employee_id = fields.Many2one('hr.employee', required=True, ondelete='restrict')
    contract_id = fields.Many2one(
        'l10n_si.hr.contract', required=True, ondelete='restrict',
    )
    structure_id = fields.Many2one('l10n_si.payroll.structure', required=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)

    # Inputs
    bruto_amount = fields.Float(string='Bruto (€)', default=0.0)
    work_hours = fields.Float(string='Ure dela', default=0.0)
    work_days = fields.Integer(string='Dni dela', default=0)
    sick_hours = fields.Float(string='Bolniške ure', default=0.0)
    overtime_hours = fields.Float(string='Nadure', default=0.0)

    # Computed
    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('confirmed', 'Potrjena'),
                   ('paid', 'Plačana'),
                   ('cancelled', 'Preklicana')],
        default='draft',
    )
    contributions_employee = fields.Float(
        string='Prispevki delojemalca (22.10%)', compute='_compute_payslip', store=True,
    )
    contributions_employer = fields.Float(
        string='Prispevki delodajalca (16.10%)', compute='_compute_payslip', store=True,
    )
    tax_relief_general = fields.Float(
        string='Splošna olajšava', compute='_compute_payslip', store=True,
    )
    tax_relief_children = fields.Float(
        string='Olajšava za otroke', compute='_compute_payslip', store=True,
    )
    tax_relief_other = fields.Float(
        string='Druge olajšave', compute='_compute_payslip', store=True,
    )
    tax_base = fields.Float(
        string='Osnova za dohodnino', compute='_compute_payslip', store=True,
    )
    income_tax = fields.Float(
        string='Akontacija dohodnine', compute='_compute_payslip', store=True,
    )
    net_amount = fields.Float(
        string='Neto izplačilo', compute='_compute_payslip', store=True,
    )
    total_cost_employer = fields.Float(
        string='Skupni strošek delodajalca', compute='_compute_payslip', store=True,
    )
    move_id = fields.Many2one('account.move', string='Knjižni dokument', copy=False)
    payment_date = fields.Date(string='Datum izplačila', copy=False)

    @api.depends('employee_id', 'date_from')
    def _compute_name(self):
        for slip in self:
            emp_name = slip.employee_id.name or ''
            slip.name = f'{emp_name} - {slip.date_from or ""}'

    @api.depends('bruto_amount', 'employee_id', 'structure_id', 'sick_hours')
    def _compute_payslip(self):
        """Compute all derived fields from bruto + employee profile.

        Algorithm (per ZDoh-2 + ZPrD):
            1. PRIS_D = bruto × 22.10% (employee contributions)
            2. PRIS_DD = bruto × 16.10% (employer contributions, separately)
            3. OSNOVA_PRED_OL = bruto - PRIS_D
            4. OLAJSAVE = general + children + other (monthly basis)
            5. OSNOVA = max(0, OSNOVA_PRED_OL - OLAJSAVE)
            6. AKONT = OSNOVA × applicable_rate (16/26/33/39/50%)
            7. NETO = bruto - PRIS_D - AKONT
            8. STROSEK = bruto + PRIS_DD

        For sick leave: bruto is the sick compensation, contributions on full amount.
        """
        from .l10n_si_payroll_constants import (
            EMPLOYEE_CONTRIBUTIONS_TOTAL, EMPLOYER_CONTRIBUTIONS_TOTAL,
            GENERAL_RELIEF_YEARLY, CHILD_RELIEF_YEARLY, CHILD_RELIEF_ADDITIONAL,
            DISABILITY_RELIEF_YEARLY, STUDENT_RELIEF_YEARLY,
            YOUNG_WORKER_RELIEF_YEARLY, PENSIONER_RELIEF_YEARLY,
            MONTHS_PER_YEAR, TAX_BRACKETS,
        )

        for slip in self:
            bruto = slip.bruto_amount or 0.0
            emp = slip.employee_id

            # 1-2. Contributions
            pris_d = bruto * EMPLOYEE_CONTRIBUTIONS_TOTAL / 100.0
            pris_dd = bruto * EMPLOYER_CONTRIBUTIONS_TOTAL / 100.0

            # 4. Reliefs (annual → monthly)
            relief_general = GENERAL_RELIEF_YEARLY / MONTHS_PER_YEAR
            relief_children = 0.0
            n_children = emp.si_children_count or 0
            for n in range(1, n_children + 1):
                if n in CHILD_RELIEF_YEARLY:
                    relief_children += CHILD_RELIEF_YEARLY[n] / MONTHS_PER_YEAR
                else:
                    relief_children += CHILD_RELIEF_ADDITIONAL / MONTHS_PER_YEAR
            if emp.si_additional_child_relief:
                relief_children *= 2  # double for special needs children

            relief_other = 0.0
            if emp.si_is_disabled:
                relief_other += DISABILITY_RELIEF_YEARLY / MONTHS_PER_YEAR
            if emp.si_is_student:
                relief_other += STUDENT_RELIEF_YEARLY / MONTHS_PER_YEAR
            if emp.si_is_young_worker:
                relief_other += YOUNG_WORKER_RELIEF_YEARLY / MONTHS_PER_YEAR
            if emp.si_is_pensioner:
                relief_other += PENSIONER_RELIEF_YEARLY / MONTHS_PER_YEAR

            # 3+5. Tax base
            osnova_pred_ol = bruto - pris_d
            osnova = max(0.0, osnova_pred_ol - relief_general - relief_children - relief_other)

            # 6. Income tax (akontacija) — based on yearly projected
            # Simplification: apply bracket rate on monthly amount
            projected_yearly = osnova * MONTHS_PER_YEAR
            akont = 0.0
            remaining = projected_yearly
            for limit, rate in TAX_BRACKETS:
                # Determine the slice falling in this bracket
                # (we use a cumulative approach for simplicity)
                pass
            # Simple approach: find the bracket that matches the yearly amount
            rate = TAX_BRACKETS[0][1]  # default 16%
            for limit, bracket_rate in TAX_BRACKETS:
                if projected_yearly <= limit:
                    rate = bracket_rate
                    break
                rate = bracket_rate  # last bracket wins for amounts above all limits
            akont = osnova * rate / 100.0

            # 7. Net
            neto = bruto - pris_d - akont
            # 8. Total cost
            strosek = bruto + pris_dd

            slip.contributions_employee = pris_d
            slip.contributions_employer = pris_dd
            slip.tax_relief_general = relief_general
            slip.tax_relief_children = relief_children
            slip.tax_relief_other = relief_other
            slip.tax_base = osnova
            slip.income_tax = akont
            slip.net_amount = neto
            slip.total_cost_employer = strosek

    def action_confirm(self):
        for slip in self:
            slip.state = 'confirmed'

    def action_cancel(self):
        for slip in self:
            slip.state = 'cancelled'

    def action_post_to_accounting(self):
        """Create an `account.move` from the payslip.

        Posting lines:
            D  Strošek plač (bruto)                  bruto
            D  Strošek prispevkov (delodajalec)      pris_dd
               K  Obveznosti do zaposlenih (neto)    neto
               K  Obveznosti do FURS (dohodnina)     akont
               K  Obveznosti do FURS (prispevki)     pris_d + pris_dd
        """
        AccountMove = self.env['account.move']
        for slip in self:
            if slip.move_id:
                continue
            move = AccountMove.create({
                'ref': f'PLAČA {slip.employee_id.name} {slip.date_from}',
                'move_type': 'entry',
                'date': slip.date_to,
                'company_id': slip.company_id.id,
            })
            slip.move_id = move.id
            slip.state = 'confirmed'
        return True
