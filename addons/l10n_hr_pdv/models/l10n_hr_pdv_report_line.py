# -*- coding: utf-8 -*-
"""Per-invoice line items for the Croatian PDV report (Knjiga PDV-a).

Each l10n_hr.pdv.report.line represents a single posted account.move
that falls within the parent report's period, with the VAT amount
grouped by rate (25%, 13%, 5%) and direction (output/input).
"""
from odoo import api, fields, models

# Croatian VAT rates (PDV stope)
PDV_RATE_25 = 25.0
PDV_RATE_13 = 13.0
PDV_RATE_5 = 5.0

# EU country codes (excluding HR) — used to detect intra-Community
# acquisitions and supplies.
EU_COUNTRY_CODES = frozenset([
    'AT', 'BE', 'BG', 'CY', 'CZ', 'DE', 'DK', 'EE', 'ES', 'FI', 'FR',
    'GR', 'HU', 'IE', 'IT', 'LT', 'LU', 'LV', 'MT', 'NL', 'PL', 'PT',
    'RO', 'SE', 'SI', 'SK',
])


class L10nHrPdvReportLine(models.Model):
    _name = 'l10n_hr.pdv.report.line'
    _description = 'Croatian PDV Report Line (per-invoice Knjiga PDV-a)'
    _order = 'date, move_id'

    report_id = fields.Many2one(
        'l10n_hr.pdv.report', string='PDV izvještaj',
        required=True, ondelete='cascade', index=True,
    )
    company_id = fields.Many2one(
        related='report_id.company_id', store=True, index=True,
    )
    move_id = fields.Many2one(
        'account.move', string='Dokument', required=True, ondelete='restrict',
    )
    move_type = fields.Selection(related='move_id.move_type', store=True)
    date = fields.Date(string='Datum', required=True)
    name = fields.Char(string='Broj dokumenta', related='move_id.name', store=True)
    partner_id = fields.Many2one(
        'res.partner', string='Partner', related='move_id.partner_id', store=True,
    )
    partner_vat = fields.Char(string='Partner OIB/VAT', store=True)
    partner_country_code = fields.Char(string='Država partnera', store=True)

    # Direction: out_invoice/out_refund → output VAT (Izlazni PDV)
    #          in_invoice/in_refund  → input VAT (Ulazni PDV)
    direction = fields.Selection(
        selection=[('output', 'Izlazni PDV'),
                   ('input', 'Ulazni PDV')],
        string='Smjer', required=True,
    )

    # Base (porezna osnovica) and tax (porez) per rate
    base_25 = fields.Monetary(string='Osnovica 25%', default=0.0, currency_field='currency_id')
    tax_25 = fields.Monetary(string='PDV 25%', default=0.0, currency_field='currency_id')
    base_13 = fields.Monetary(string='Osnovica 13%', default=0.0, currency_field='currency_id')
    tax_13 = fields.Monetary(string='PDV 13%', default=0.0, currency_field='currency_id')
    base_5 = fields.Monetary(string='Osnovica 5%', default=0.0, currency_field='currency_id')
    tax_5 = fields.Monetary(string='PDV 5%', default=0.0, currency_field='currency_id')

    # Exempt / out-of-scope base (oslobođene isporuke / neoporezive nabave)
    base_exempt = fields.Monetary(
        string='Oslobođeno / izvan opsega', default=0.0, currency_field='currency_id',
    )

    # Flags
    is_reverse_charge = fields.Boolean(string='Obrnuti porezni teret', default=False)
    is_eu_acquisition = fields.Boolean(string='EU nabava', default=False)
    is_eu_supply = fields.Boolean(string='EU isporuka', default=False)

    base_total = fields.Monetary(
        string='Ukupna osnovica', compute='_compute_totals', store=True,
        currency_field='currency_id',
    )
    tax_total = fields.Monetary(
        string='Ukupni PDV', compute='_compute_totals', store=True,
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        'res.currency', related='report_id.currency_id', store=True,
    )

    @api.depends('base_25', 'base_13', 'base_5', 'base_exempt',
                 'tax_25', 'tax_13', 'tax_5')
    def _compute_totals(self):
        for line in self:
            line.base_total = (
                line.base_25 + line.base_13 + line.base_5 + line.base_exempt
            )
            line.tax_total = line.tax_25 + line.tax_13 + line.tax_5

    @api.model
    def _classify_partner(self, partner):
        """Determine EU flags for a partner based on country code.

        Returns a dict: {country_code, is_eu, is_hr}
        """
        country = partner.country_id if partner else None
        code = (country.code or '').upper() if country else ''
        return {
            'country_code': code,
            'is_eu': code in EU_COUNTRY_CODES,
            'is_hr': code == 'HR',
        }

    @api.model
    def _rate_bucket(self, rate):
        """Map an arbitrary tax rate to one of the 3 Croatian PDV buckets.

        Returns one of: '25', '13', '5', or None (other/exempt).
        """
        try:
            r = float(rate)
        except (TypeError, ValueError):
            return None
        if abs(r - PDV_RATE_25) < 0.01:
            return '25'
        if abs(r - PDV_RATE_13) < 0.01:
            return '13'
        if abs(r - PDV_RATE_5) < 0.01:
            return '5'
        return None
