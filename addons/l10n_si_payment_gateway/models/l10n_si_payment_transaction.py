# -*- coding: utf-8 -*-
"""Payment transaction - ena plačilna transakcija."""
from odoo import api, fields, models


class L10nSiPaymentTransaction(models.Model):
    _name = 'l10n_si.payment.transaction'
    _description = 'Slovenian Payment Transaction'
    _inherit = ['mail.thread']
    _order = 'create_date DESC'

    name = fields.Char(copy=False, readonly=True, default='/')
    config_id = fields.Many2one('l10n_si.payment.config', required=True, ondelete='restrict')
    company_id = fields.Many2one(related='config_id.company_id', store=True)

    # Povezava
    partner_id = fields.Many2one('res.partner', string='Gost/Stranka')
    move_id = fields.Many2one('account.move', string='Račun')
    hotel_reservation_id = fields.Many2one('l10n_si.hotel.reservation', string='Rezervacija')
    hotel_folio_id = fields.Many2one('l10n_si.hotel.folio', string='Folio')

    # Znesek
    amount = fields.Monetary(required=True, currency_field='currency_id')
    fee_amount = fields.Monetary(compute='_compute_fee', store=True, currency_field='currency_id',
                                   string='Provizija')
    net_amount = fields.Monetary(compute='_compute_fee', store=True, currency_field='currency_id',
                                   string='Neto znesek')
    currency_id = fields.Many2one('res.currency', related='config_id.currency_id', store=True)

    # Status
    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('pending', 'V teku'),
                   ('completed', 'Zaključeno'),
                   ('failed', 'Neuspešno'),
                   ('refunded', 'Vrnjeno'),
                   ('cancelled', 'Preklicano')],
        default='draft',
        tracking=True,
    )

    # External reference
    external_transaction_id = fields.Char(string='ID transakcije pri procesorju', copy=False, readonly=True)
    payment_url = fields.Char(string='URL za plačilo', copy=False, readonly=True)

    # Dates
    initiated_on = fields.Datetime(default=fields.Datetime.now, readonly=True)
    completed_on = fields.Datetime(readonly=True, copy=False)
    refunded_on = fields.Datetime(readonly=True, copy=False)

    # 3DS
    requires_3ds = fields.Boolean(default=False)
    _3ds_authenticated = fields.Boolean(default=False)

    # Error
    error_message = fields.Text(readonly=True, copy=False)

    notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('l10n_si.payment.transaction') or '/'
        return super().create(vals_list)

    @api.depends('amount', 'config_id')
    def _compute_fee(self):
        for tx in self:
            cfg = tx.config_id
            tx.fee_amount = (tx.amount * cfg.fee_percent / 100) + cfg.fee_fixed
            tx.net_amount = tx.amount - tx.fee_amount

    def action_initiate(self):
        """Initiate payment with the provider."""
        for tx in self:
            tx.state = 'pending'
            tx.initiated_on = fields.Datetime.now()
            if tx.config_id.provider in ('cash', 'trr'):
                # Manual payment - just mark pending
                pass
            else:
                # V produkciji: pravi API klic
                tx.external_transaction_id = f'{tx.config_id.provider}_{tx.name}'
                tx.requires_3ds = tx.config_id.supports_3ds

    def action_complete(self):
        """Mark payment as completed and reconcile with invoice."""
        for tx in self:
            tx.write({
                'state': 'completed',
                'completed_on': fields.Datetime.now(),
            })
            # Auto-reconcile with invoice if linked
            if tx.move_id and tx.move_id.state == 'posted':
                tx._reconcile_with_invoice()

    def action_refund(self):
        """Refund the payment."""
        for tx in self:
            if not tx.config_id.supports_refund:
                continue
            tx.write({
                'state': 'refunded',
                'refunded_on': fields.Datetime.now(),
            })

    def action_fail(self):
        self.write({'state': 'failed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def _reconcile_with_invoice(self):
        """Create payment and reconcile with the linked invoice."""
        self.ensure_one()
        if not self.move_id:
            return
        payment = self.env['account.payment'].create({
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': self.partner_id.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'journal_id': self.config_id.journal_id.id,
            'payment_method_line_id': False,
            'date': fields.Date.today(),
        })
        payment.action_post()
        # Reconcile
        lines_to_reconcile = (self.move_id.line_ids + payment.move_id.line_ids).filtered(
            lambda l: l.account_id.account_type in ('asset_receivable', 'liability_payable')
        )
        if lines_to_reconcile:
            lines_to_reconcile.reconcile()

    def action_generate_payment_link(self):
        """Generate a payment link URL to send to customer."""
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        self.payment_url = f'{base_url}/payment/pay/{self.name}'
        return {
            'type': 'ir.actions.act_url',
            'url': self.payment_url,
            'target': 'self',
        }
