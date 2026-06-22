# -*- coding: utf-8 -*-
"""Transaction - one tax charge for one guest for one stay."""
from odoo import api, fields, models


class L10nSiTouristTaxTransaction(models.Model):
    _name = 'l10n_si.tourist.tax.transaction'
    _description = 'Slovenian Tourist Tax Transaction'
    _order = 'date DESC'

    name = fields.Char(copy=False, readonly=True, default='/')
    date = fields.Date(required=True, default=fields.Date.today)
    municipality_id = fields.Many2one(
        'l10n_si.tourist.tax.municipality', required=True, ondelete='restrict',
    )

    # Guest
    partner_id = fields.Many2one('res.partner', string='Gost')
    guest_name = fields.Char(string='Ime gosta')
    guest_age = fields.Integer(string='Starost')
    guest_country_id = fields.Many2one('res.country', string='Država gosta')

    # Stay
    nights = fields.Integer(required=True, default=1, string='Nočitve (obračunane)')
    actual_nights = fields.Integer(string='Dejanske nočitve')
    chargeable_nights = fields.Integer(
        string='Obračunane nočitve',
        compute='_compute_chargeable',
        store=True,
    )

    # Rate
    rate = fields.Float(string='Taksa na noč (EUR)', required=True)
    tax_amount = fields.Monetary(
        string='Skupaj taksa (EUR)',
        compute='_compute_amount', store=True, currency_field='currency_id',
    )
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)

    # Source document
    res_model = fields.Char(string='Izvirni dokument')
    res_id = fields.Integer(string='ID dokumenta')
    move_id = fields.Many2one('account.move', string='Račun')
    move_line_id = fields.Many2one('account.move.line', string='Postavka računa')

    # Status
    state = fields.Selection(
        selection=[('draft', 'Osnutek'),
                   ('posted', 'Knjiženo'),
                   ('reported', 'Prijavljeno občini'),
                   ('paid', 'Plačano občini')],
        default='draft',
        tracking=True,
    )

    # Exemptions
    is_exempt = fields.Boolean(
        string='Oproščeno',
        help='True if guest is exempt (disabled, tour leader, etc.).',
    )
    exemption_reason = fields.Selection(
        selection=[('disabled', 'Invalid (kartica)'),
                   ('tour_leader', 'Vodnik skupine'),
                   ('diplomat', 'Diplomat'),
                   ('transit', 'Tranzit (< 24h)'),
                   ('resident', 'Stalni prebivalec občine'),
                   ('other', 'Drugo')],
    )
    exemption_notes = fields.Text()

    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('l10n_si.tourist.tax.transaction') or '/'
        return super().create(vals_list)

    @api.depends('nights', 'municipality_id')
    def _compute_chargeable(self):
        for tx in self:
            max_nights = tx.municipality_id.max_chargeable_nights or 7
            tx.chargeable_nights = min(tx.nights, max_nights)

    @api.depends('chargeable_nights', 'rate', 'is_exempt')
    def _compute_amount(self):
        for tx in self:
            if tx.is_exempt:
                tx.tax_amount = 0.0
            else:
                tx.tax_amount = tx.chargeable_nights * tx.rate

    def action_post_to_accounting(self):
        """Create a journal entry to record the tax collected."""
        for tx in self:
            if not tx.municipality_id.tax_account_id or tx.move_line_id:
                continue
            # In real implementation: create journal entry on the tax account
            tx.state = 'posted'

    def action_report_to_municipality(self):
        """Mark as reported to the municipality (for monthly/quarterly returns)."""
        self.write({'state': 'reported'})

    def action_mark_paid(self):
        """Mark as paid to the municipality."""
        self.write({'state': 'paid'})

    @api.model
    def calculate_for_stay(self, municipality_id, guests_data, nights):
        """Calculate total tourist tax for a stay with multiple guests.

        Args:
            municipality_id: int - municipality record ID
            guests_data: list of dicts with keys: age, is_exempt, exemption_reason
            nights: int - actual nights stayed

        Returns:
            tuple: (total_tax, list_of_transaction_vals)
        """
        municipality = self.browse(municipality_id)
        if not municipality:
            return 0.0, []

        max_nights = municipality.max_chargeable_nights or 7
        chargeable_nights = min(nights, max_nights)
        total = 0.0
        transactions = []

        for guest in guests_data:
            if guest.get('is_exempt'):
                rate = 0.0
                amount = 0.0
            else:
                age = guest.get('age', 30)
                rate = municipality.get_rate_for_age(municipality.id, age)
                amount = chargeable_nights * rate

            total += amount
            transactions.append({
                'municipality_id': municipality_id,
                'nights': nights,
                'chargeable_nights': chargeable_nights,
                'rate': rate,
                'tax_amount': amount,
                'guest_age': age,
                'is_exempt': guest.get('is_exempt', False),
                'exemption_reason': guest.get('exemption_reason'),
            })

        return total, transactions
