# -*- coding: utf-8 -*-
"""Financial ratios - ključni kazalci uspešnosti podjetja."""
from odoo import api, fields, models


class L10nSiFinancialRatio(models.Model):
    _name = 'l10n_si.financial.ratio'
    _description = 'Slovenian Financial Ratio'
    _order = 'year DESC'

    name = fields.Char(compute='_compute_name', store=True)
    year = fields.Integer(required=True, default=lambda self: fields.Date.today().year)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # === Likvidnost ===
    current_ratio = fields.Float(string='Tekoče razmerje (current ratio)',
                                   help='Sredstva / Kratkoročne obveznosti. > 2 = dobro.')
    quick_ratio = fields.Float(string='Hitro razmerje (quick ratio)',
                                 help='(Sredstva - zaloge) / Kratkoročne obveznosti. > 1 = dobro.')
    cash_ratio = fields.Float(string='Denarno razmerje',
                                help='Denar / Kratkoročne obveznosti.')

    # === Rentabilnost ===
    roa = fields.Float(string='ROA - return on assets',
                         help='Čisti dobiček / Skupna sredstva × 100. > 5% = dobro.')
    roe = fields.Float(string='ROE - return on equity',
                         help='Čisti dobiček / Lastniški kapital × 100. > 10% = dobro.')
    ros = fields.Float(string='ROS - return on sales',
                         help='Čisti dobiček / Prihodki × 100.')
    roi = fields.Float(string='ROI - return on investment')

    # === Zadolženost ===
    debt_ratio = fields.Float(string='Stopnja zadolženosti',
                                help='Obveznosti / Skupna sredstva × 100. < 60% = dobro.')
    debt_equity_ratio = fields.Float(string='Dolg/kapital',
                                       help='Skupne obveznosti / Lastniški kapital.')
    interest_coverage = fields.Float(string='Pokritje obresti',
                                       help='EBIT / Obrestne stroške. > 3 = dobro.')

    # === Aktivnost ===
    asset_turnover = fields.Float(string='Promet sredstev',
                                    help='Prihodki / Skupna sredstva.')
    inventory_turnover = fields.Float(string='Promet zalog')
    receivables_turnover = fields.Float(string='Promet terjatev')
    days_sales_outstanding = fields.Float(string='DSO - dni do izterjave',
                                            help='365 / Promet terjatev.')

    # === Vrednosti za izračun (input) ===
    total_assets = fields.Monetary(string='Skupna sredstva', currency_field='currency_id')
    current_assets = fields.Monetary(string='Kratkoročna sredstva', currency_field='currency_id')
    inventory = fields.Monetary(string='Zaloge', currency_field='currency_id')
    cash = fields.Monetary(string='Denar', currency_field='currency_id')
    total_liabilities = fields.Monetary(string='Skupne obveznosti', currency_field='currency_id')
    current_liabilities = fields.Monetary(string='Kratkoročne obveznosti', currency_field='currency_id')
    equity = fields.Monetary(string='Lastniški kapital', currency_field='currency_id')
    net_profit = fields.Monetary(string='Čisti dobiček', currency_field='currency_id')
    revenue = fields.Monetary(string='Prihodki', currency_field='currency_id')
    ebit = fields.Monetary(string='EBIT', currency_field='currency_id')
    interest_expense = fields.Monetary(string='Obrestni stroški', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)

    notes = fields.Text()

    @api.depends('year')
    def _compute_name(self):
        for r in self:
            r.name = f'{r.year} - Kazalniki'

    @api.onchange('current_assets', 'current_liabilities')
    def _onchange_liquidity(self):
        for r in self:
            r.current_ratio = r.current_assets / r.current_liabilities if r.current_liabilities else 0
            r.quick_ratio = (r.current_assets - r.inventory) / r.current_liabilities if r.current_liabilities else 0
            r.cash_ratio = r.cash / r.current_liabilities if r.current_liabilities else 0

    @api.onchange('net_profit', 'total_assets', 'equity', 'revenue')
    def _onchange_profitability(self):
        for r in self:
            r.roa = (r.net_profit / r.total_assets * 100) if r.total_assets else 0
            r.roe = (r.net_profit / r.equity * 100) if r.equity else 0
            r.ros = (r.net_profit / r.revenue * 100) if r.revenue else 0

    @api.onchange('total_liabilities', 'total_assets', 'equity', 'ebit', 'interest_expense')
    def _onchange_debt(self):
        for r in self:
            r.debt_ratio = (r.total_liabilities / r.total_assets * 100) if r.total_assets else 0
            r.debt_equity_ratio = (r.total_liabilities / r.equity) if r.equity else 0
            r.interest_coverage = (r.ebit / r.interest_expense) if r.interest_expense else 0

    @api.onchange('revenue', 'total_assets')
    def _onchange_activity(self):
        for r in self:
            r.asset_turnover = (r.revenue / r.total_assets) if r.total_assets else 0
            if r.receivables_turnover:
                r.days_sales_outstanding = 365 / r.receivables_turnover

    def action_compute_from_accounting(self):
        """Izračunaj vrednosti iz SRS poročil."""
        SrsReport = self.env['l10n_si.srs.report']
        for ratio in self:
            # Najdi SRS bilanco za to leto
            balance = SrsReport.search([
                ('year', '=', ratio.year),
                ('report_type', '=', 'balance_sheet'),
                ('company_id', '=', ratio.company_id.id),
            ], limit=1)
            income = SrsReport.search([
                ('year', '=', ratio.year),
                ('report_type', '=', 'income_statement'),
                ('company_id', '=', ratio.company_id.id),
            ], limit=1)
            if balance:
                ratio.total_assets = balance.total_assets
                ratio.total_liabilities = balance.total_liabilities
            if income:
                ratio.revenue = income.total_revenue
                ratio.net_profit = income.net_profit
            # Trigger onchange methods
            ratio._onchange_liquidity()
            ratio._onchange_profitability()
            ratio._onchange_debt()
            ratio._onchange_activity()
