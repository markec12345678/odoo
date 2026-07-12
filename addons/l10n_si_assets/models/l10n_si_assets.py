# -*- coding: utf-8 -*-
from odoo import api, fields, models


class L10nSiAssetCategory(models.Model):
    _name = 'l10n_si.asset.category'
    _description = 'Slovenian Asset Category'
    _order = 'name'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, size=8)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company',
        default=lambda self: self.env.company, required=True)

    depreciation_method = fields.Selection(
        selection=[('linear', 'Linearna'),
                   ('declining', 'Degresivna'),
                   ('declining_switch', 'Degresivna → linearna')],
        default='linear', required=True)
    depreciation_rate = fields.Float(default=20.0, string='Stopnja amortizacije (%)')
    useful_life_years = fields.Integer(default=5, string='Obratovalna doba (let)')

    account_asset_id = fields.Many2one('account.account', string='Konto osnovnega sredstva')
    account_depreciation_id = fields.Many2one('account.account', string='Konto amortizacije')
    account_expense_id = fields.Many2one('account.account', string='Konto stroška amortizacije')

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 'Code must be unique per company.'),
    ]


class L10nSiAsset(models.Model):
    _name = 'l10n_si.asset'
    _description = 'Slovenian Fixed Asset'
    _inherit = ['mail.thread']
    _order = 'acquisition_date DESC'

    name = fields.Char(required=True, tracking=True)
    number = fields.Char(copy=False, readonly=True, default='/')
    code = fields.Char(string='Inventarna številka', required=True, size=20)
    category_id = fields.Many2one('l10n_si.asset.category', required=True, ondelete='restrict')
    company_id = fields.Many2one('res.company', string='Company',
        default=lambda self: self.env.company, required=True)

    acquisition_date = fields.Date(required=True, default=fields.Date.today)
    acquisition_value = fields.Monetary(required=True, default=0.0, currency_field='currency_id',
        string='Nabavna vrednost (EUR)')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)

    # Depreciation
    depreciation_method = fields.Selection(related='category_id.depreciation_method', store=True)
    depreciation_rate = fields.Float(related='category_id.depreciation_rate', store=True)
    useful_life_years = fields.Integer(related='category_id.useful_life_years', store=True)
    accumulated_depreciation = fields.Monetary(compute='_compute_depreciation', store=False,
        string='Akumulirana amortizacija', currency_field='currency_id')
    book_value = fields.Monetary(compute='_compute_depreciation', store=False,
        string='Knjigovodska vrednost', currency_field='currency_id')
    monthly_depreciation = fields.Monetary(compute='_compute_depreciation', store=False,
        string='Mesečna amortizacija', currency_field='currency_id')

    # Status
    state = fields.Selection(
        selection=[('draft', 'Osnutek'), ('active', 'V uporabi'),
                   ('disposed', 'Odtujeno'), ('written_off', 'Odpisano')],
        default='draft', tracking=True)

    disposal_date = fields.Date(readonly=True, copy=False)
    disposal_value = fields.Monetary(readonly=True, copy=False, currency_field='currency_id')

    location = fields.Char(string='Lokacija')
    responsible_id = fields.Many2one('res.users', string='Odgovorna oseba')
    serial_number = fields.Char(string='Serijska številka')
    notes = fields.Text()

    depreciation_line_ids = fields.One2many('l10n_si.asset.depreciation.line', 'asset_id',
        string='Amortizacijske postavke')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('number', '/') == '/':
                vals['number'] = self.env['ir.sequence'].next_by_code('l10n_si.asset') or '/'
        return super().create(vals_list)

    def _compute_depreciation(self):
        for asset in self:
            accumulated = sum(asset.depreciation_line_ids.mapped('amount'))
            asset.accumulated_depreciation = accumulated
            asset.book_value = asset.acquisition_value - accumulated
            if asset.depreciation_method == 'linear' and asset.useful_life_years:
                asset.monthly_depreciation = asset.acquisition_value / (asset.useful_life_years * 12)
            elif asset.depreciation_rate:
                asset.monthly_depreciation = asset.book_value * (asset.depreciation_rate / 100) / 12
            else:
                asset.monthly_depreciation = 0.0

    def action_activate(self):
        self.write({'state': 'active'})

    def action_dispose(self):
        self.write({'state': 'disposed', 'disposal_date': fields.Date.today()})

    def action_generate_monthly_depreciation(self):
        """Generate monthly depreciation entries."""
        from datetime import date
        today = date.today()
        first_of_month = today.replace(day=1)
        active_assets = self.filtered(lambda a: a.state == 'active' and a.monthly_depreciation > 0)
        if not active_assets:
            return
        # Single search for ALL existing depreciation lines this month
        # (was N+1: one search per asset — fixed to 1 query for all assets)
        existing_asset_ids = self.env['l10n_si.asset.depreciation.line'].search([
            ('asset_id', 'in', active_assets.ids),
            ('date', '=', first_of_month),
        ]).mapped('asset_id.id')
        # Create depreciation lines for assets that don't have one yet
        vals_list = [
            {
                'asset_id': asset.id,
                'date': first_of_month,
                'amount': asset.monthly_depreciation,
                'depreciation_type': 'monthly',
            }
            for asset in active_assets
            if asset.id not in existing_asset_ids
        ]
        if vals_list:
            self.env['l10n_si.asset.depreciation.line'].create(vals_list)


class L10nSiAssetDepreciationLine(models.Model):
    _name = 'l10n_si.asset.depreciation.line'
    _description = 'Slovenian Asset Depreciation Line'
    _order = 'date DESC'

    asset_id = fields.Many2one('l10n_si.asset', required=True, ondelete='cascade')
    date = fields.Date(required=True)
    amount = fields.Monetary(required=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='asset_id.currency_id', store=True)
    depreciation_type = fields.Selection(
        selection=[('monthly', 'Mesečna'), ('annual', 'Letna'),
                   ('disposal', 'Ob odtujitvi'), ('write_off', 'Odpis')],
        default='monthly', required=True)
    move_id = fields.Many2one('account.move', string='Knjižni dokument')
    notes = fields.Text()
