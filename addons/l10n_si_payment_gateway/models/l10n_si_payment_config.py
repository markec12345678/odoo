# -*- coding: utf-8 -*-
"""Payment gateway configuration - one per provider."""
from odoo import api, fields, models


class L10nSiPaymentConfig(models.Model):
    _name = 'l10n_si.payment.config'
    _description = 'Slovenian Payment Gateway Configuration'
    _order = 'sequence'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    provider = fields.Selection(
        selection=[('activa', 'Activa Pay (SI)'),
                   ('stripe', 'Stripe'),
                   ('paypal', 'PayPal'),
                   ('upn', 'UPN (SEPA)'),
                   ('trr', 'TRR (bančno nakazilo)'),
                   ('cash', 'Gotovina'),
                   ('voucher', 'Darilni vavčer')],
        required=True,
        default='trr',
    )

    # Credentials
    api_key = fields.Char(string='API ključ')
    api_secret = fields.Char(string='API skrivnost')
    merchant_id = fields.Char(string='Merchant ID')
    webhook_secret = fields.Char(string='Webhook skrivnost')
    iban = fields.Char(string='IBAN (za TRR/UPN)')
    bic = fields.Char(string='BIC (za TRR/UPN)')

    # Environment
    environment = fields.Selection(
        selection=[('test', 'Testno okolje'),
                   ('prod', 'Produkcija')],
        default='test',
        required=True,
    )
    endpoint_url = fields.Char(string='API endpoint URL')

    # Settings
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, required=True)
    supports_3ds = fields.Boolean(string='3D Secure', default=True)
    supports_refund = fields.Boolean(default=True)
    supports_recurring = fields.Boolean(default=False)
    min_amount = fields.Float(default=0.0, string='Min. znesek (EUR)')
    max_amount = fields.Float(default=10000.0, string='Max. znesek (EUR)')
    fee_percent = fields.Float(default=0.0, string='Provizija (%)')
    fee_fixed = fields.Float(default=0.0, string='Fiksna provizija (EUR)')

    # Journal
    journal_id = fields.Many2one('account.journal', string='Dnevnik plačil',
                                   domain="[('type', 'in', ('bank', 'cash'))]")

    # Stats
    transaction_ids = fields.One2many('l10n_si.payment.transaction', 'config_id', string='Transakcije')
    transaction_count = fields.Integer(compute='_compute_stats', store=False)
    total_processed = fields.Monetary(compute='_compute_stats', store=False,
                                       string='Skupno procesirano', currency_field='currency_id')

    @api.depends('transaction_ids')
    def _compute_stats(self):
        for c in self:
            txs = c.transaction_ids.filtered(lambda t: t.state == 'completed')
            c.transaction_count = len(txs)
            c.total_processed = sum(txs.mapped('amount'))

    def action_test_connection(self):
        """Test API connection to provider."""
        import requests
        for cfg in self:
            if cfg.provider in ('cash', 'trr'):
                continue  # No API to test
            try:
                response = requests.get(cfg.endpoint_url, timeout=10)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Connection Test',
                        'message': f'HTTP {response.status_code}',
                        'type': 'success' if response.status_code == 200 else 'danger',
                    },
                }
            except Exception as e:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {'title': 'Error', 'message': str(e), 'type': 'danger'},
                }
