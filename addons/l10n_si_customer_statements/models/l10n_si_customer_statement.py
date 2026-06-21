# -*- coding: utf-8 -*-
from odoo import api, fields, models


class L10nSiCustomerStatement(models.Model):
    """Generated customer statement — one per partner per period."""
    _name = 'l10n_si.customer.statement'
    _description = 'Slovenian Customer Statement'
    _order = 'date_to DESC, partner_id'

    name = fields.Char(compute='_compute_name', store=True)
    partner_id = fields.Many2one('res.partner', required=True, ondelete='restrict')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)

    # Opening + closing balance
    opening_balance = fields.Monetary(default=0.0, currency_field='currency_id')
    closing_balance = fields.Monetary(default=0.0, currency_field='currency_id')
    invoiced_amount = fields.Monetary(default=0.0, currency_field='currency_id')
    paid_amount = fields.Monetary(default=0.0, currency_field='currency_id')

    # Aging buckets at date_to
    aging_0_30 = fields.Monetary(default=0.0, currency_field='currency_id')
    aging_31_60 = fields.Monetary(default=0.0, currency_field='currency_id')
    aging_61_90 = fields.Monetary(default=0.0, currency_field='currency_id')
    aging_90_plus = fields.Monetary(default=0.0, currency_field='currency_id')

    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id,
        required=True,
    )
    pdf_attachment_id = fields.Many2one('ir.attachment', readonly=True, copy=False)
    sent = fields.Boolean(default=False, copy=False)
    sent_on = fields.Datetime(readonly=True, copy=False)

    line_ids = fields.One2many(
        'l10n_si.customer.statement.line', 'statement_id', string='Lines', readonly=True,
    )

    @api.depends('partner_id', 'date_from', 'date_to')
    def _compute_name(self):
        for stmt in self:
            stmt.name = f'{stmt.partner_id.name or ""} - {stmt.date_from or ""} do {stmt.date_to or ""}'

    def action_send_email(self):
        """Send the statement PDF to the customer via email."""
        for stmt in self:
            if not stmt.pdf_attachment_id:
                continue
            template = self.env.ref(
                'l10n_si_customer_statements.email_template_statement',
                raise_if_not_found=False,
            )
            if template:
                template.send_mail(stmt.id, force_send=True)
                stmt.write({'sent': True, 'sent_on': fields.Datetime.now()})


class L10nSiCustomerStatementLine(models.Model):
    """One line in the statement (invoice, payment, or adjustment)."""
    _name = 'l10n_si.customer.statement.line'
    _description = 'Slovenian Customer Statement Line'
    _order = 'date, id'

    statement_id = fields.Many2one('l10n_si.customer.statement', required=True, ondelete='cascade')
    date = fields.Date(required=True)
    move_id = fields.Many2one('account.move', string='Document')
    ref = fields.Char(string='Reference')
    debit = fields.Monetary(currency_field='currency_id')
    credit = fields.Monetary(currency_field='currency_id')
    balance = fields.Monetary(currency_field='currency_id', compute='_compute_balance', store=True)
    currency_id = fields.Many2one(related='statement_id.currency_id')
    line_type = fields.Selection(
        selection=[('invoice', 'Račun'),
                   ('payment', 'Plačilo'),
                   ('credit_note', 'Dobropis'),
                   ('adjustment', 'Popravek')],
        default='invoice',
    )

    @api.depends('debit', 'credit')
    def _compute_balance(self):
        for line in self:
            line.balance = line.debit - line.credit
