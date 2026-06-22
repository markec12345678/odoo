# -*- coding: utf-8 -*-
"""Budget - letni proračun po oddelkih."""
from odoo import api, fields, models


class L10nSiBudget(models.Model):
    _name = 'l10n_si.budget'
    _description = 'Slovenian Budget'
    _inherit = ['mail.thread']
    _order = 'year DESC, department'

    name = fields.Char(compute='_compute_name', store=True)
    number = fields.Char(copy=False, readonly=True, default='/')
    year = fields.Integer(required=True, default=lambda self: fields.Date.today().year + 1)
    department = fields.Selection(
        selection=[('rooms', 'Sobe'),
                   ('fb', 'F&B (gostinstvo)'),
                   ('wellness', 'Wellness/Spa'),
                   ('events', 'Dogodki'),
                   ('housekeeping', 'Hišništvo'),
                   ('maintenance', 'Vzdrževanje'),
                   ('sales_marketing', 'Prodaja in marketing'),
                   ('admin', 'Uprava'),
                   ('it', 'IT'),
                   ('hr', 'Kadrovska'),
                   ('other', 'Drugo')],
        required=True,
        default='rooms',
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analitični konto')

    # Status
    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('submitted', 'Predlagano'),
                   ('approved', 'Odobreno'),
                   ('active', 'Aktivno'),
                   ('closed', 'Zaključeno'),
                   ('cancelled', 'Preklicano')],
        default='draft',
        tracking=True,
    )

    # Linije
    line_ids = fields.One2many('l10n_si.budget.line', 'budget_id', string='Postavke proračuna')

    # Skupne vrednosti
    total_revenue_planned = fields.Monetary(compute='_compute_totals', store=True,
                                              string='Prihodek (načrt)',
                                              currency_field='currency_id')
    total_expense_planned = fields.Monetary(compute='_compute_totals', store=True,
                                              string='Stroški (načrt)',
                                              currency_field='currency_id')
    total_profit_planned = fields.Monetary(compute='_compute_totals', store=True,
                                             string='Dobiček (načrt)',
                                             currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)

    # Realizacija
    total_revenue_actual = fields.Monetary(compute='_compute_actuals', store=False,
                                             string='Prihodek (dejansko)')
    total_expense_actual = fields.Monetary(compute='_compute_actuals', store=False,
                                             string='Stroški (dejansko)')
    total_profit_actual = fields.Monetary(compute='_compute_actuals', store=False,
                                            string='Dobiček (dejansko)')

    # Odstopanja
    revenue_variance_percent = fields.Float(compute='_compute_variance', store=False,
                                              string='Prihodek odstopanje (%)')
    expense_variance_percent = fields.Float(compute='_compute_variance', store=False,
                                              string='Stroški odstopanje (%)')
    profit_variance_percent = fields.Float(compute='_compute_variance', store=False,
                                             string='Dobiček odstopanje (%)')

    notes = fields.Text()
    approved_by = fields.Many2one('res.users', readonly=True, copy=False)
    approved_on = fields.Datetime(readonly=True, copy=False)

    _sql_constraints = [
        ('year_dept_company_uniq', 'unique(year, department, company_id)',
         'Budget already exists for this year/department/company.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', '/') == '/':
                vals['number'] = self.env['ir.sequence'].next_by_code('l10n_si.budget') or '/'
        return super().create(vals_list)

    @api.depends('year', 'department')
    def _compute_name(self):
        labels = dict(self._fields['department'].selection)
        for b in self:
            b.name = f'{b.year} - {labels.get(b.department, b.department)}'

    @api.depends('line_ids.amount_planned')
    def _compute_totals(self):
        for b in self:
            revenue_lines = b.line_ids.filtered(lambda l: l.line_type == 'revenue')
            expense_lines = b.line_ids.filtered(lambda l: l.line_type == 'expense')
            b.total_revenue_planned = sum(revenue_lines.mapped('amount_planned'))
            b.total_expense_planned = sum(expense_lines.mapped('amount_planned'))
            b.total_profit_planned = b.total_revenue_planned - b.total_expense_planned

    def _compute_actuals(self):
        """Realizacija iz account.analytic.line + account.move.line."""
        for b in self:
            # V produkciji: dejansko branje iz analytic.line
            b.total_revenue_actual = 0.0
            b.total_expense_actual = 0.0
            b.total_profit_actual = b.total_revenue_actual - b.total_expense_actual

    def _compute_variance(self):
        for b in self:
            if b.total_revenue_planned:
                b.revenue_variance_percent = (
                    (b.total_revenue_actual - b.total_revenue_planned) / b.total_revenue_planned * 100
                )
            else:
                b.revenue_variance_percent = 0.0
            if b.total_expense_planned:
                b.expense_variance_percent = (
                    (b.total_expense_actual - b.total_expense_planned) / b.total_expense_planned * 100
                )
            else:
                b.expense_variance_percent = 0.0
            if b.total_profit_planned:
                b.profit_variance_percent = (
                    (b.total_profit_actual - b.total_profit_planned) / b.total_profit_planned * 100
                )
            else:
                b.profit_variance_percent = 0.0

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_approve(self):
        for b in self:
            b.write({
                'state': 'approved',
                'approved_by': self.env.user.id,
                'approved_on': fields.Datetime.now(),
            })

    def action_activate(self):
        self.write({'state': 'active'})

    def action_close(self):
        self.write({'state': 'closed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})
