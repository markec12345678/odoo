# -*- coding: utf-8 -*-
"""POS Order - FURS integracija + room charge."""
from odoo import fields, models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    # FURS
    l10n_si_zoi = fields.Char(string='ZOI', copy=False, readonly=True,
                                help='Zaščitna oznaka izdajatelja računa.')
    l10n_si_eor = fields.Char(string='EOR', copy=False, readonly=True,
                                help='Enkratna identifikacijska oznaka računa.')
    l10n_si_fiscal_state = fields.Selection(
        selection=[('pending', 'Čaka'),
                   ('submitted', 'Poslano'),
                   ('error', 'Napaka')],
        copy=False, readonly=True,
    )

    # Hotelski folio (room charge)
    l10n_si_hotel_folio_id = fields.Many2one(
        'l10n_si.hotel.folio', string='Hotelski folio',
        help='Če je stranka gost hotela, se račun zaračuna na folio.',
    )

    # Turistična taksa
    l10n_si_tourist_tax_amount = fields.Monetary(
        string='Turistična taksa', copy=False, readonly=True,
        currency_field='currency_id',
    )

    def _process_order(self, pos_order_vals):
        """Override POS order processing to add FURS + room charge."""
        order = super()._process_order(pos_order_vals)
        if order.config_id.si_fiscal_enabled:
            order._si_generate_zoi_and_submit_furs()
        if order.config_id.si_add_tourist_tax and order.config_id.si_municipality_id:
            order._si_add_tourist_tax()
        return order

    def _si_generate_zoi_and_submit_furs(self):
        """Generiraj ZOI in pošlji FURS za vsako POS naročilo."""
        for order in self:
            if order.l10n_si_zoi:
                continue
            # Reuse FURS submission logic from l10n_si_fiscal
            # (this assumes the order has been converted to account.move first)
            order.l10n_si_fiscal_state = 'pending'
            # V produkciji: klic l10n_si_fiscal.account_move._si_fiscal_submit_to_furs
            # preko povezanega account.move

    def _si_add_tourist_tax(self):
        """Dodaj turistično takso na POS račun glede na občino iz config-a."""
        municipality = self.config_id.si_municipality_id
        if not municipality:
            return
        # Zelo poenostavljeno - v produkciji bi preverili št. oseb, nočitve
        tax_amount = municipality.rate_adult  # 1 nočitev, 1 oseba
        self.l10n_si_tourist_tax_amount = tax_amount

    def action_si_resubmit_furs(self):
        """Ročno vnovično pošiljanje v FURS pri napakah."""
        for order in self:
            order._si_generate_zoi_and_submit_furs()

    def action_si_charge_to_room(self):
        """Preusmeri plačilo na hotelski folio."""
        for order in self:
            if not order.l10n_si_hotel_folio_id:
                continue
            # Premakni znesek na folio kot service line
            self.env['l10n_si.hotel.folio.line'].create({
                'folio_id': order.l10n_si_hotel_folio_id.id,
                'service_id': False,  # generičen
                'description': f'POS račun {order.pos_reference}',
                'quantity': 1,
                'unit_price': order.amount_total,
            })
