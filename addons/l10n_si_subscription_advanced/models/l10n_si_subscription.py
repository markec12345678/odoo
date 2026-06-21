# -*- coding: utf-8 -*-
"""Subscription — one customer's subscription to one plan."""
from datetime import timedelta

from odoo import _, api, fields, models


class L10nSiSubscription(models.Model):
    _name = 'l10n_si.subscription'
    _description = 'Slovenian Subscription'
    _inherit = ['mail.thread']
    _order = 'date_start DESC'

    name = fields.Char(compute='_compute_name', store=True)
    number = fields.Char(copy=False, readonly=True, default='/')
    partner_id = fields.Many2one('res.partner', required=True, tracking=True)
    plan_id = fields.Many2one('l10n_si.subscription.plan', required=True, tracking=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    # Dates
    date_start = fields.Date(required=True, default=fields.Date.today, tracking=True)
    date_end = fields.Date(compute='_compute_date_end', store=True, readonly=False, tracking=True)
    date_cancelled = fields.Date(readonly=True, copy=False)
    next_invoice_date = fields.Date(required=True, default=fields.Date.today)

    # Pricing (copied from plan, can be overridden)
    recurring_price = fields.Float(required=True, default=0.0)
    recurring_interval = fields.Integer(required=True, default=1)
    recurring_rule = fields.Selection(
        selection=[('daily', 'Dnevno'),
                   ('weekly', 'Tedensko'),
                   ('monthly', 'Mesečno'),
                   ('quarterly', 'Kvartalno'),
                   ('yearly', 'Letno')],
        default='monthly', required=True,
    )

    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('trial', 'Trial'),
                   ('active', 'Aktivna'),
                   ('paused', 'Pavzirana'),
                   ('cancelled', 'Preklicana'),
                   ('expired', 'Potekla')],
        default='draft',
        tracking=True,
    )

    invoice_ids = fields.Many2many('account.move', string='Invoices', readonly=True)
    invoice_count = fields.Integer(compute='_compute_invoice_count')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', '/') == '/':
                vals['number'] = self.env['ir.sequence'].next_by_code('l10n_si.subscription') or '/'
            # Copy defaults from plan
            if vals.get('plan_id') and not vals.get('recurring_price'):
                plan = self.env['l10n_si.subscription.plan'].browse(vals['plan_id'])
                vals.setdefault('recurring_price', plan.recurring_price)
                vals.setdefault('recurring_interval', plan.recurring_interval)
                vals.setdefault('recurring_rule', plan.recurring_rule)
        return super().create(vals_list)

    @api.depends('partner_id', 'number')
    def _compute_name(self):
        for sub in self:
            sub.name = f'{sub.number or ""} - {sub.partner_id.name or ""}'

    @api.depends('date_start', 'recurring_interval', 'recurring_rule')
    def _compute_date_end(self):
        for sub in self:
            if not sub.date_start:
                continue
            if sub.recurring_rule == 'daily':
                sub.date_end = sub.date_start + timedelta(days=sub.recurring_interval)
            elif sub.recurring_rule == 'weekly':
                sub.date_end = sub.date_start + timedelta(weeks=sub.recurring_interval)
            elif sub.recurring_rule == 'monthly':
                sub.date_end = sub.date_start + timedelta(days=30 * sub.recurring_interval)
            elif sub.recurring_rule == 'quarterly':
                sub.date_end = sub.date_start + timedelta(days=90 * sub.recurring_interval)
            elif sub.recurring_rule == 'yearly':
                sub.date_end = sub.date_start + timedelta(days=365 * sub.recurring_interval)

    def _compute_invoice_count(self):
        for sub in self:
            sub.invoice_count = len(sub.invoice_ids)

    def action_activate(self):
        for sub in self:
            sub.state = 'active'
            sub.next_invoice_date = sub.date_start

    def action_pause(self):
        self.write({'state': 'paused'})

    def action_resume(self):
        self.write({'state': 'active'})

    def action_cancel(self):
        for sub in self:
            sub.write({
                'state': 'cancelled',
                'date_cancelled': fields.Date.today(),
            })

    def action_generate_invoice(self):
        """Generate an invoice for the current period."""
        Invoice = self.env['account.move']
        for sub in self:
            if sub.state not in ('active', 'trial'):
                continue
            invoice = Invoice.create({
                'move_type': 'out_invoice',
                'partner_id': sub.partner_id.id,
                'invoice_date': sub.next_invoice_date,
                'company_id': sub.company_id.id,
                'invoice_line_ids': [(0, 0, {
                    'product_id': sub.plan_id.product_id.id,
                    'name': f'{sub.plan_id.name} ({sub.recurring_rule})',
                    'quantity': 1,
                    'price_unit': sub.recurring_price,
                })],
            })
            sub.invoice_ids = [(4, invoice.id)]
            # Advance next_invoice_date
            sub._advance_next_invoice_date()
            sub.message_post(body=_('Generiran račun %s za obdobje od %s.') % (
                invoice.name, sub.next_invoice_date,
            ))

    def _advance_next_invoice_date(self):
        for sub in self:
            delta = {
                'daily': timedelta(days=sub.recurring_interval),
                'weekly': timedelta(weeks=sub.recurring_interval),
                'monthly': timedelta(days=30 * sub.recurring_interval),
                'quarterly': timedelta(days=90 * sub.recurring_interval),
                'yearly': timedelta(days=365 * sub.recurring_interval),
            }.get(sub.recurring_rule)
            if delta:
                sub.next_invoice_date = sub.next_invoice_date + delta

    @api.model
    def _cron_generate_invoices(self):
        """Cron: generate invoices for all active subscriptions due today."""
        today = fields.Date.today()
        due_subs = self.search([
            ('state', 'in', ['active', 'trial']),
            ('next_invoice_date', '<=', today),
        ])
        for sub in due_subs:
            try:
                sub.action_generate_invoice()
            except Exception as e:  # noqa: BLE001
                sub.message_post(body=f'⚠️ Napaka pri generiranju računa: {e}')
