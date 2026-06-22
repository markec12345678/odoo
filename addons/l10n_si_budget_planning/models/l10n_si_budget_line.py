# -*- coding: utf-8 -*-
"""Budget line - ena postavka v proračunu."""
from odoo import api, fields, models


class L10nSiBudgetLine(models.Model):
    _name = 'l10n_si.budget.line'
    _description = 'Slovenian Budget Line'
    _order = 'budget_id, sequence, name'

    budget_id = fields.Many2one('l10n_si.budget', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='budget_id.company_id', store=True)

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)

    # Tip
    line_type = fields.Selection(
        selection=[('revenue', 'Prihodek'),
                   ('expense', 'Strošek')],
        required=True,
        default='expense',
    )

    # Kategorija stroška/prihodka
    category = fields.Selection(
        selection=[('personnel', 'Osebje (plače, prispevki)'),
                   ('materials', 'Materiali'),
                   ('energy', 'Energija (el., plin, voda)'),
                   ('marketing', 'Marketing'),
                   ('maintenance', 'Vzdrževanje'),
                   ('depreciation', 'Amortizacija'),
                   ('rent', 'Najemnine'),
                   ('insurance', 'Zavarovanja'),
                   ('travel', 'Službena potovanja'),
                   ('training', 'Izobraževanja'),
                   ('it', 'IT stroški'),
                   ('other', 'Drugo'),
                   # Prihodki
                   ('rooms_revenue', 'Prihodek od sob'),
                   ('fb_revenue', 'Prihodek od F&B'),
                   ('wellness_revenue', 'Prihodek od wellness'),
                   ('events_revenue', 'Prihodek od dogodkov'),
                   ('other_revenue', 'Drugi prihodki')],
        required=True,
        default='materials',
    )

    # Mesečni načrt (12 mesecev)
    amount_planned = fields.Monetary(required=True, default=0.0,
                                       string='Letni načrt (EUR)',
                                       currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='budget_id.currency_id', store=True)

    # Mesečni razcep (če želimo bolj natančno)
    jan_amount = fields.Monetary(default=0.0, currency_field='currency_id')
    feb_amount = fields.Monetary(default=0.0, currency_field='currency_id')
    mar_amount = fields.Monetary(default=0.0, currency_field='currency_id')
    apr_amount = fields.Monetary(default=0.0, currency_field='currency_id')
    may_amount = fields.Monetary(default=0.0, currency_field='currency_id')
    jun_amount = fields.Monetary(default=0.0, currency_field='currency_id')
    jul_amount = fields.Monetary(default=0.0, currency_field='currency_id')
    aug_amount = fields.Monetary(default=0.0, currency_field='currency_id')
    sep_amount = fields.Monetary(default=0.0, currency_field='currency_id')
    oct_amount = fields.Monetary(default=0.0, currency_field='currency_id')
    nov_amount = fields.Monetary(default=0.0, currency_field='currency_id')
    dec_amount = fields.Monetary(default=0.0, currency_field='currency_id')

    # Realizacija
    amount_actual = fields.Monetary(default=0.0, string='Realizacija (EUR)',
                                      currency_field='currency_id', readonly=True, copy=False)
    variance_amount = fields.Monetary(compute='_compute_variance', store=True,
                                        string='Odstopanje (EUR)')
    variance_percent = fields.Float(compute='_compute_variance', store=True,
                                      string='Odstopanje (%)')

    # Opombe
    notes = fields.Text()

    @api.depends('amount_planned', 'amount_actual')
    def _compute_variance(self):
        for line in self:
            line.variance_amount = line.amount_actual - line.amount_planned
            if line.amount_planned:
                line.variance_percent = (line.variance_amount / line.amount_planned) * 100
            else:
                line.variance_percent = 0.0

    @api.onchange('jan_amount', 'feb_amount', 'mar_amount', 'apr_amount',
                  'may_amount', 'jun_amount', 'jul_amount', 'aug_amount',
                  'sep_amount', 'oct_amount', 'nov_amount', 'dec_amount')
    def _onchange_monthly_amounts(self):
        """Avtomatsko seštej mesece v letni načrt."""
        for line in self:
            line.amount_planned = (
                line.jan_amount + line.feb_amount + line.mar_amount + line.apr_amount +
                line.may_amount + line.jun_amount + line.jul_amount + line.aug_amount +
                line.sep_amount + line.oct_amount + line.nov_amount + line.dec_amount
            )

    def action_distribute_evenly(self):
        """Porazdeli letni znesek enakomerno na 12 mesecev."""
        for line in self:
            monthly = line.amount_planned / 12
            for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                          'jul', 'aug', 'sep', 'oct', 'nov', 'dec']:
                line[f'{month}_amount'] = monthly
