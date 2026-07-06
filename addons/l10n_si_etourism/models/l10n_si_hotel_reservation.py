# -*- coding: utf-8 -*-
"""Hotel reservation hooks: auto-register/deregister guests with AJPES."""
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class L10nSiHotelReservation(models.Model):
    _inherit = 'l10n_si.hotel.reservation'

    def action_check_in(self):
        result = super().action_check_in()
        self._l10n_si_etourism_register_guests()
        return result

    def action_check_out(self):
        result = super().action_check_out()
        self._l10n_si_etourism_deregister_guests()
        return result

    def _l10n_si_etourism_get_establishment(self):
        self.ensure_one()
        Establishment = self.env['l10n_si.etourism.establishment']
        return Establishment.search([
            ('company_id', '=', self.company_id.id), ('active', '=', True),
            ('establishment_type', 'in', ['hotel', 'private_room', 'farm']),
        ], limit=1)

    def _l10n_si_etourism_register_guests(self):
        Registration = self.env['l10n_si.etourism.guest.registration']
        for res in self:
            if not res.company_id.l10n_si_etourism_auto_register:
                continue
            establishment = res._l10n_si_etourism_get_establishment()
            if not establishment or not establishment.auto_register:
                continue
            existing = Registration.search([
                ('hotel_reservation_id', '=', res.id), ('partner_id', '=', res.partner_id.id),
                ('ajpes_status', 'in', ['draft', 'pending', 'submitted']),
            ])
            if existing:
                continue
            reg = Registration.create({
                'establishment_id': establishment.id, 'partner_id': res.partner_id.id,
                'arrival_date': res.check_in, 'hotel_reservation_id': res.id,
                'hotel_folio_id': res.folio_id.id if res.folio_id else False,
                'res_model': 'l10n_si.hotel.reservation', 'res_id': res.id, 'company_id': res.company_id.id,
            })
            reg.action_submit_to_ajpes()

    def _l10n_si_etourism_deregister_guests(self):
        Registration = self.env['l10n_si.etourism.guest.registration']
        for res in self:
            if not res.company_id.l10n_si_etourism_auto_deregister:
                continue
            regs = Registration.search([('hotel_reservation_id', '=', res.id), ('ajpes_status', '=', 'submitted')])
            for reg in regs:
                reg.departure_date = res.check_out
                reg.action_deregister_with_ajpes()
