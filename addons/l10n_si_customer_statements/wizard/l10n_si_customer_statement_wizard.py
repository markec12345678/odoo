# -*- coding: utf-8 -*-
"""Generate customer statements for a period."""
import calendar
from datetime import date

from odoo import api, fields, models


class L10nSiCustomerStatementWizard(models.TransientModel):
    _name = 'l10n_si.customer.statement.wizard'
    _description = 'Generate Customer Statements'

    year = fields.Integer(required=True, default=lambda self: fields.Date.today().year)
    month = fields.Integer(required=True, default=lambda self: fields.Date.today().month)
    partner_ids = fields.Many2many('res.partner', string='Stranke (prazno = vse)')
    send_email = fields.Boolean(string='Pošlji po e-pošti', default=False)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    def action_generate(self):
        self.ensure_one()
        date_from = date(self.year, self.month, 1)
        last_day = calendar.monthrange(self.year, self.month)[1]
        date_to = date(self.year, self.month, last_day)

        partners = self.partner_ids or self.env['res.partner'].search([
            ('customer_rank', '>', 0),
            ('company_id', 'in', [False, self.company_id.id]),
        ])

        Statement = self.env['l10n_si.customer.statement']
        for partner in partners:
            stmt = Statement.create({
                'partner_id': partner.id,
                'company_id': self.company_id.id,
                'date_from': date_from,
                'date_to': date_to,
            })
            stmt._compute_lines_and_balances()
            if self.send_email:
                stmt.action_send_email()
        return {'type': 'ir.actions.act_window_close'}


# Attach helper to L10nSiCustomerStatement via monkey patch (kept here for locality)
from odoo.addons.l10n_si_customer_statements.models.l10n_si_customer_statement import (
    L10nSiCustomerStatement,
)


@api.model
def _compute_lines_and_balances(self):
    """Populate lines + balances from account.move.line for this partner + period."""
    self.ensure_one()
    MoveLine = self.env['account.move.line']
    domain = [
        ('partner_id', '=', self.partner_id.id),
        ('date', '<=', self.date_to),
        ('parent_state', '=', 'posted'),
        ('account_id.account_type', 'in', ('asset_receivable', 'liability_payable')),
    ]
    lines_data = []
    opening_balance = 0.0
    invoiced = 0.0
    paid = 0.0

    for ml in MoveLine.search(domain + [('date', '<', self.date_from)]):
        opening_balance += ml.balance

    for ml in MoveLine.search(domain + [('date', '>=', self.date_from), ('date', '<=', self.date_to)]):
        line_type = 'invoice'
        if ml.payment_id:
            line_type = 'payment'
        elif ml.move_id.move_type == 'out_refund':
            line_type = 'credit_note'
        lines_data.append((0, 0, {
            'date': ml.date,
            'move_id': ml.move_id.id,
            'ref': ml.ref or ml.move_id.name,
            'debit': ml.debit,
            'credit': ml.credit,
            'line_type': line_type,
        }))
        if ml.debit > 0:
            invoiced += ml.debit
        if ml.credit > 0:
            paid += ml.credit

    # Aging buckets at date_to
    aging_0_30 = aging_31_60 = aging_61_90 = aging_90_plus = 0.0
    open_lines = MoveLine.search(domain + [('date', '<=', self.date_to), ('reconciled', '=', False)])
    from datetime import timedelta
    for ml in open_lines:
        if ml.balance == 0:
            continue
        days_overdue = (self.date_to - ml.date).days
        if days_overdue <= 30:
            aging_0_30 += ml.balance
        elif days_overdue <= 60:
            aging_31_60 += ml.balance
        elif days_overdue <= 90:
            aging_61_90 += ml.balance
        else:
            aging_90_plus += ml.balance

    closing = opening_balance + invoiced - paid
    self.write({
        'opening_balance': opening_balance,
        'invoiced_amount': invoiced,
        'paid_amount': paid,
        'closing_balance': closing,
        'aging_0_30': aging_0_30,
        'aging_31_60': aging_31_60,
        'aging_61_90': aging_61_90,
        'aging_90_plus': aging_90_plus,
        'line_ids': lines_data,
    })


L10nSiCustomerStatement._compute_lines_and_balances = _compute_lines_and_balances
