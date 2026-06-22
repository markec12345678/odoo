# -*- coding: utf-8 -*-
"""SRS report - slovenska računovodska poročila."""
from odoo import api, fields, models


class L10nSiSrsReport(models.Model):
    _name = 'l10n_si.srs.report'
    _description = 'Slovenian SRS Report'
    _inherit = ['mail.thread']
    _order = 'year DESC, report_type'

    name = fields.Char(compute='_compute_name', store=True)
    number = fields.Char(copy=False, readonly=True, default='/')
    year = fields.Integer(required=True, default=lambda self: fields.Date.today().year)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    report_type = fields.Selection(
        selection=[('balance_sheet', 'Bilanca stanja'),
                   ('income_statement', 'Izid poslovanja'),
                   ('cash_flow', 'Denarni tokovi'),
                   ('capital_changes', 'Spremembe kapitala'),
                   ('vat_return', 'Davčna napoved (DDV-O)')],
        required=True,
        default='balance_sheet',
    )

    # Časovno obdobje
    date_from = fields.Date(required=True, default=lambda self: f'{fields.Date.today().year}-01-01')
    date_to = fields.Date(required=True, default=lambda self: f'{fields.Date.today().year}-12-31')

    # Status
    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('computed', 'Izračunano'),
                   ('reviewed', 'Pregledano'),
                   ('submitted', 'Predloženo AJPES'),
                   ('accepted', 'AJPES sprejel'),
                   ('rejected', 'AJPES zavrgnil'),
                   ('archived', 'Arhivirano')],
        default='draft',
        tracking=True,
    )

    # Postavke
    line_ids = fields.One2many('l10n_si.srs.report.line', 'report_id', string='Postavke')

    # Skupne vrednosti
    total_assets = fields.Monetary(compute='_compute_totals', store=True, string='Skupaj sredstva',
                                     currency_field='currency_id')
    total_liabilities = fields.Monetary(compute='_compute_totals', store=True,
                                          string='Skupaj obveznosti in kapital',
                                          currency_field='currency_id')
    total_revenue = fields.Monetary(compute='_compute_totals', store=True, string='Skupaj prihodki',
                                      currency_field='currency_id')
    total_expenses = fields.Monetary(compute='_compute_totals', store=True, string='Skupaj odhodki',
                                       currency_field='currency_id')
    net_profit = fields.Monetary(compute='_compute_totals', store=True, string='Dobiček iz poslovanja',
                                   currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)

    # AJPES submission
    ajpes_message_id = fields.Char(readonly=True, copy=False)
    ajpes_submitted_on = fields.Datetime(readonly=True, copy=False)
    ajpes_response = fields.Text(readonly=True, copy=False)
    pdf_attachment_id = fields.Many2one('ir.attachment', string='PDF poročilo')

    notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', '/') == '/':
                vals['number'] = self.env['ir.sequence'].next_by_code('l10n_si.srs.report') or '/'
        return super().create(vals_list)

    @api.depends('year', 'report_type')
    def _compute_name(self):
        labels = dict(self._fields['report_type'].selection)
        for r in self:
            r.name = f'{r.year} - {labels.get(r.report_type, r.report_type)}'

    def _compute_totals(self):
        for r in self:
            r.total_assets = sum(r.line_ids.filtered(lambda l: l.balance_section == 'assets').mapped('amount'))
            r.total_liabilities = sum(r.line_ids.filtered(lambda l: l.balance_section == 'liabilities').mapped('amount'))
            r.total_revenue = sum(r.line_ids.filtered(lambda l: l.income_section == 'revenue').mapped('amount'))
            r.total_expenses = sum(r.line_ids.filtered(lambda l: l.income_section == 'expense').mapped('amount'))
            r.net_profit = r.total_revenue - r.total_expenses

    def action_compute(self):
        """Izračunaj vrednosti postavk iz account.move.line."""
        for report in self:
            for line in report.line_ids:
                line._compute_amount(report.date_from, report.date_to)
            report.state = 'computed'

    def action_review(self):
        self.write({'state': 'reviewed'})

    def action_submit_ajpes(self):
        """Submit poročilo k AJPES-u."""
        for r in self:
            # V produkciji: klic AJPES eDavki API
            r.write({
                'state': 'submitted',
                'ajpes_submitted_on': fields.Datetime.now(),
                'ajpes_message_id': f'AJPES-{r.number}-{fields.Datetime.now().strftime("%Y%m%d%H%M%S")}',
            })

    def action_mark_accepted(self):
        self.write({'state': 'accepted'})

    def action_mark_rejected(self):
        self.write({'state': 'rejected'})


class L10nSiSrsReportLine(models.Model):
    _name = 'l10n_si.srs.report.line'
    _description = 'Slovenian SRS Report Line'
    _order = 'report_id, sequence'

    report_id = fields.Many2one('l10n_si.srs.report', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    name = fields.Char(required=True, translate=True)

    # SRS klasifikacija
    srs_code = fields.Char(required=True, size=8, string='SRS koda',
                              help='npr. A0001, B0020, 100 (kontni razred)')
    account_codes = fields.Char(string='Konti (CSV)',
                                  help='npr. "010,011,012" - konti, ki seštejemo za to postavko')

    # Sekcija
    balance_section = fields.Selection(
        selection=[('assets', 'Sredstva'),
                   ('liabilities', 'Obveznosti in kapital')],
        default='assets',
    )
    income_section = fields.Selection(
        selection=[('revenue', 'Prihodek'),
                   ('expense', 'Odhodek')],
        default='expense',
    )

    # Vrednost
    amount = fields.Monetary(default=0.0, string='Znesek (EUR)', currency_field='currency_id')
    amount_previous_year = fields.Monetary(default=0.0, string='Znesek lani (EUR)',
                                              currency_field='currency_id')
    variance = fields.Monetary(compute='_compute_variance', store=True, string='Razlika (EUR)')
    variance_percent = fields.Float(compute='_compute_variance', store=True, string='Razlika (%)')
    currency_id = fields.Many2one('res.currency', related='report_id.currency_id', store=True)

    notes = fields.Text()

    @api.depends('amount', 'amount_previous_year')
    def _compute_variance(self):
        for l in self:
            l.variance = l.amount - l.amount_previous_year
            if l.amount_previous_year:
                l.variance_percent = (l.variance / l.amount_previous_year) * 100
            else:
                l.variance_percent = 0.0

    def _compute_amount(self, date_from, date_to):
        """Izračunaj znesek iz account.move.line glede na konte."""
        for line in self:
            if not line.account_codes:
                continue
            account_list = [c.strip() for c in line.account_codes.split(',')]
            moves = self.env['account.move.line'].search([
                ('account_id.code', 'in', account_list),
                ('date', '>=', date_from),
                ('date', '<=', date_to),
                ('parent_state', '=', 'posted'),
            ])
            # Neto = debit - credit (za sredstva); obratno za obveznosti
            debit = sum(moves.mapped('debit'))
            credit = sum(moves.mapped('credit'))
            if line.balance_section == 'assets':
                line.amount = debit - credit
            elif line.balance_section == 'liabilities':
                line.amount = credit - debit
            elif line.income_section == 'revenue':
                line.amount = credit - debit  # prihodki so kreditno
            else:  # expense
                line.amount = debit - credit  # odhodki so debetno
